"""
cascade_calculator.py — Cascading Disruption Graph Engine (CDGE).

Algorithm:
  1. Map disruption location → source node UUID
  2. BFS on REVERSED graph → upstream nodes (suppliers/factory that can no longer
     ship through the disrupted node)
  3. BFS on FORWARD graph → downstream nodes (buyers waiting for goods)
  4. Downstream gets DOWNSTREAM_HOP_OFFSET extra hops so they show lower risk
     than immediate upstream (port disruption hurts factory more than buyer 22 days away)
  5. risk_score = severity_factor × 0.6^effective_hop × confidence_score
  6. financial_exposure_inr = active_shipment_value_inr × risk_score

Verified expected output — Scenario 1 (JNPT, severity=4, confidence=0.95):
  severity_factor = 4/5 = 0.80
  JNPT Port           hop=0   risk = 0.80 × 1.000 × 0.95 = 0.760
  AuroraTex Factory   hop=1   risk = 0.80 × 0.600 × 0.95 = 0.456
  Yarn Supplier A/B   hop=2   risk = 0.80 × 0.360 × 0.95 = 0.274
  Dye Chem Supplier   hop=2   risk = 0.80 × 0.360 × 0.95 = 0.274
  Rotterdam Port      hop=3   risk = 0.80 × 0.216 × 0.95 = 0.164
"""

import logging
from typing import Optional
import networkx as nx

logger = logging.getLogger(__name__)

# Key: location string from disruption_events.affected_location
# Value: node name exactly as stored in supply_chain_nodes.name (None = not in graph)
LOCATION_TO_NODE_NAME: dict[str, Optional[str]] = {
    "JNPT":      "JNPT Port",
    "Mumbai":    "JNPT Port",
    "Chennai":   "Dye Chemical Supplier",
    "Surat":     "AuroraTex Factory",
    "Rotterdam": "Rotterdam Port",
    "Red Sea":   "Rotterdam Port",  # Red Sea crisis impacts Rotterdam lane
    "Mundra":    None,              # Not in base graph
}

# Extra hops added to downstream nodes to reflect they're less immediately
# impacted than upstream nodes (cargo at sea has 22 days buffer)
DOWNSTREAM_HOP_OFFSET: int = 2


class CascadeCalculator:

    def __init__(self, graph: nx.DiGraph):
        if not isinstance(graph, nx.DiGraph):
            raise TypeError("graph must be a NetworkX DiGraph instance")
        if graph.number_of_nodes() == 0:
            raise ValueError(
                "Graph has no nodes — run seed_data.py first, "
                "then verify with: python -c \"from graph_builder import *; "
                "print_graph_summary(build_graph())\""
            )
        self.graph = graph

    # ── Public API ────────────────────────────────────────────────────────────

    def calculate(self, disruption_event: dict) -> list[dict]:
        """
        Compute cascade risk for every node given a disruption event dict.

        Args:
            disruption_event: {
                'affected_location': str,   e.g. 'JNPT'
                'severity':          int,   1–5
                'confidence_score':  float  0.0–1.0
            }

        Returns:
            List of impact dicts sorted by risk_score descending:
            {
                node_id:                str,
                node_name:              str,
                node_type:              str,
                risk_score:             float,
                financial_exposure_inr: int,
                time_to_impact_hours:   float,
                cascade_hop:            int
            }
        """
        if not disruption_event:
            logger.warning("Empty disruption_event passed to calculate()")
            return []

        source_node = self._find_source_node(
            disruption_event.get("affected_location", "")
        )
        if source_node is None:
            logger.warning(
                f"Location '{disruption_event.get('affected_location')}' "
                "not mapped to any graph node — cascade aborted"
            )
            return []

        # Validate + clamp severity to [1, 5]
        try:
            severity = max(1, min(5, int(disruption_event.get("severity", 1))))
        except (TypeError, ValueError):
            severity = 1

        # Validate + clamp confidence to [0.0, 1.0]
        try:
            confidence = max(0.0, min(1.0, float(disruption_event.get("confidence_score", 0.8))))
        except (TypeError, ValueError):
            confidence = 0.8

        severity_factor = severity / 5.0

        # BFS in both directions from source node
        upstream_hops   = self._bfs_upstream(source_node)
        downstream_hops = self._bfs_downstream(source_node)

        results: list[dict] = []
        for node_id, node_data in self.graph.nodes(data=True):
            effective_hop = self._effective_hop(
                node_id, source_node, upstream_hops, downstream_hops
            )

            # Risk attenuates 40% per hop (× 0.6 per hop)
            attenuation = 0.6 ** effective_hop
            risk_score  = round(
                max(0.0, min(1.0, severity_factor * attenuation * confidence)),
                3,
            )

            active_value       = int(node_data.get("active_shipment_value_inr") or 0)
            financial_exposure = max(0, int(active_value * risk_score))
            time_to_impact     = self._time_to_impact(source_node, node_id)

            results.append({
                "node_id":                node_id,
                "node_name":              str(node_data.get("name", node_id)),
                "node_type":              str(node_data.get("node_type", "unknown")),
                "risk_score":             risk_score,
                "financial_exposure_inr": financial_exposure,
                "time_to_impact_hours":   time_to_impact,
                "cascade_hop":            effective_hop,
            })

        return sorted(results, key=lambda x: x["risk_score"], reverse=True)

    def get_cascade_path(self, disruption_event: dict) -> list[str]:
        """
        Returns ordered list of node UUIDs showing cascade propagation sequence.
        Person C uses this to animate the cascading effect on the map.
        Order: source node first, then by hop ascending, then by exposure descending.
        """
        results = self.calculate(disruption_event)
        if not results:
            return []

        ordered = sorted(
            results,
            key=lambda x: (x["cascade_hop"], -x["financial_exposure_inr"])
        )
        return [r["node_id"] for r in ordered]

    def find_node_by_location(self, location_name: str) -> Optional[str]:
        """Public wrapper — returns node UUID or None."""
        return self._find_source_node(location_name)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _find_source_node(self, location_name: str) -> Optional[str]:
        """
        Map location string → node UUID in the graph.
        1. Checks LOCATION_TO_NODE_NAME mapping (exact)
        2. Falls back to case-insensitive substring match on node names
        """
        if not location_name:
            return None

        if location_name in LOCATION_TO_NODE_NAME:
            target_name = LOCATION_TO_NODE_NAME[location_name]
            if target_name is None:
                return None  # Explicitly not in graph (e.g. Mundra)
            for node_id, data in self.graph.nodes(data=True):
                if data.get("name") == target_name:
                    return node_id
            logger.warning(f"Node name '{target_name}' not found in graph")
            return None

        # Fallback: fuzzy match
        location_lower = location_name.lower()
        for node_id, data in self.graph.nodes(data=True):
            if location_lower in str(data.get("name", "")).lower():
                logger.info(f"Fuzzy-matched '{location_name}' → '{data.get('name')}'")
                return node_id

        logger.warning(f"No graph node found for location: '{location_name}'")
        return None

    def _bfs_upstream(self, source_node: str) -> dict[str, int]:
        """
        BFS on the REVERSED graph from source.
        Upstream nodes = suppliers/factory that ship THROUGH the disrupted node.
        When JNPT is disrupted:
          Factory (hop 1) → can't ship goods to JNPT
          Suppliers (hop 2) → factory won't need their inputs
        """
        reversed_graph = self.graph.reverse(copy=True)
        try:
            return dict(nx.single_source_shortest_path_length(reversed_graph, source_node))
        except nx.NetworkXError as exc:
            logger.error(f"Upstream BFS failed from {source_node}: {exc}")
            return {source_node: 0}

    def _bfs_downstream(self, source_node: str) -> dict[str, int]:
        """
        BFS on the FORWARD graph from source.
        Downstream nodes = buyers/destinations waiting for goods.
        When JNPT is disrupted:
          Rotterdam (hop 1) → won't receive cargo on time
        """
        try:
            return dict(nx.single_source_shortest_path_length(self.graph, source_node))
        except nx.NetworkXError as exc:
            logger.error(f"Downstream BFS failed from {source_node}: {exc}")
            return {source_node: 0}

    def _effective_hop(
        self,
        node_id:        str,
        source_node:    str,
        upstream_hops:  dict[str, int],
        downstream_hops: dict[str, int],
    ) -> int:
        """
        Compute effective hop distance for risk attenuation:
          Source          → 0
          Upstream nodes  → actual BFS hop (primary cascade path)
          Downstream nodes→ actual hop + DOWNSTREAM_HOP_OFFSET (secondary)
          Unreachable     → 99 (negligible risk ~= 0)
        """
        if node_id == source_node:
            return 0

        up_dist   = upstream_hops.get(node_id)
        down_dist = downstream_hops.get(node_id)

        # Prefer upstream direction (higher impact) if both exist
        if up_dist is not None and up_dist > 0:
            return up_dist

        if down_dist is not None and down_dist > 0:
            return down_dist + DOWNSTREAM_HOP_OFFSET

        return 99  # Unreachable — essentially zero risk

    def _time_to_impact(self, source: str, target: str) -> float:
        """
        Hours until disruption effect reaches target from source.
        Checks forward path (downstream) first, then reverse (upstream).
        Returns 0.0 if source == target or no path exists.
        """
        if source == target:
            return 0.0

        # Forward: source → target (downstream)
        try:
            path = nx.shortest_path(
                self.graph, source, target, weight="transit_time_hours"
            )
            return round(
                sum(self.graph[u][v]["transit_time_hours"] for u, v in zip(path[:-1], path[1:])),
                1,
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Reverse: target → source (target is upstream)
        try:
            path = nx.shortest_path(
                self.graph, target, source, weight="transit_time_hours"
            )
            return round(
                sum(self.graph[u][v]["transit_time_hours"] for u, v in zip(path[:-1], path[1:])),
                1,
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        return 0.0
