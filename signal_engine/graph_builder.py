"""
graph_builder.py — Loads AuroraTex supply chain from Supabase → NetworkX DiGraph.

Graph structure:
  Nodes: keyed by UUID (str), attributes include name, node_type, lat/lng,
         active_shipment_value_inr, risk_score, is_disrupted
  Edges: directed (source → target), attributes include transit_time_hours,
         shipment_value_inr, transport_mode, is_disrupted

Edge direction = direction of goods flow:
  Yarn Supplier A   → AuroraTex Factory → JNPT Port → Rotterdam Port
  Yarn Supplier B   ↗
  Dye Chemical Supplier ↗
"""

import logging
import networkx as nx
from db_client import get_all_nodes, get_all_edges

logger = logging.getLogger(__name__)


def build_graph(company_id: str = "auroratea") -> nx.DiGraph:
    """
    Build and return a NetworkX DiGraph from Supabase node/edge data.
    Returns an empty DiGraph if no data found (caller handles this).
    Always call seed_data.py first if graph is empty.
    """
    G = nx.DiGraph()

    # ── Load nodes ────────────────────────────────────────────────────────────
    nodes = get_all_nodes(company_id)
    if not nodes:
        logger.warning(
            f"No nodes found for company_id='{company_id}'. "
            "Run: python seed_data.py"
        )
        return G

    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            logger.warning(f"Skipping node with no id: {node}")
            continue

        G.add_node(
            node_id,
            name=str(node.get("name", "")),
            node_type=str(node.get("node_type", "unknown")),
            lat=float(node.get("lat") or 0.0),
            lng=float(node.get("lng") or 0.0),
            total_inventory_value_inr=int(node.get("total_inventory_value_inr") or 0),
            active_shipment_value_inr=int(node.get("active_shipment_value_inr") or 0),
            risk_score=float(node.get("risk_score") or 0.0),
            is_disrupted=bool(node.get("is_disrupted", False)),
        )

    # ── Load edges ────────────────────────────────────────────────────────────
    edges = get_all_edges(company_id)
    skipped = 0
    for edge in edges:
        src = edge.get("source_node_id")
        tgt = edge.get("target_node_id")

        if not src or not tgt:
            logger.warning(f"Skipping edge with missing node IDs: {edge.get('id')}")
            skipped += 1
            continue

        if not G.has_node(src):
            logger.warning(f"Edge source {src} not in graph — skipping edge {edge.get('id')}")
            skipped += 1
            continue

        if not G.has_node(tgt):
            logger.warning(f"Edge target {tgt} not in graph — skipping edge {edge.get('id')}")
            skipped += 1
            continue

        transit_days = float(edge.get("transit_time_days") or 1.0)

        G.add_edge(
            src,
            tgt,
            edge_id=str(edge.get("id", "")),
            transit_time_hours=transit_days * 24.0,   # convert to hours for time_to_impact
            shipment_value_inr=int(edge.get("shipment_value_inr") or 0),
            transport_mode=str(edge.get("transport_mode") or "road"),
            is_disrupted=bool(edge.get("is_disrupted", False)),
        )

    logger.info(
        f"Graph built for '{company_id}': "
        f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        + (f" (skipped {skipped} bad edges)" if skipped else "")
    )
    return G


def print_graph_summary(G: nx.DiGraph) -> None:
    """Print a readable summary of the graph (Day 1 verification tool)."""
    print(f"\n{'='*60}")
    print(f"  AuroraTex Supply Chain Graph")
    print(f"  Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}")
    print(f"{'='*60}")
    print("\nNODES:")
    for node_id, data in G.nodes(data=True):
        print(
            f"  [{data.get('node_type', '?'):12}]  "
            f"{data.get('name', '?'):30}  "
            f"₹{data.get('active_shipment_value_inr', 0) / 100_000:.0f}L active"
        )
    print("\nEDGES (goods flow direction):")
    for src, tgt, data in G.edges(data=True):
        src_name = G.nodes[src].get("name", src[:8])
        tgt_name = G.nodes[tgt].get("name", tgt[:8])
        print(
            f"  {src_name:30} → {tgt_name:30}  "
            f"{data.get('transport_mode', '?'):5}  "
            f"{data.get('transit_time_hours', 0):.0f}h  "
            f"₹{data.get('shipment_value_inr', 0) / 100_000:.0f}L"
        )
    print()
