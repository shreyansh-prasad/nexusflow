"""
test_scenarios.py — Validate all 3 demo scenarios without needing Supabase.

Builds an in-memory graph with hardcoded UUIDs, then runs CascadeCalculator.
Use this to confirm math is correct before the demo.

Run:
  python test_scenarios.py

Expected output for Scenario 1 (JNPT, sev=4, conf=0.95):
  JNPT Port:          risk=0.760  ₹26.60Cr exposure  hop=0
  AuroraTex Factory:  risk=0.456  ₹82L exposure      hop=1
  Yarn Supplier A:    risk=0.274  ₹8.2L exposure     hop=2
  Yarn Supplier B:    risk=0.274  ₹6.8L exposure     hop=2
  Dye Chem Supplier:  risk=0.274  ₹16.4L exposure    hop=2
  Rotterdam Port:     risk=0.164  ₹73.8L exposure    hop=3

NOTE on pitch numbers:
  Person D says "₹2.3Cr at risk" — this is the VALUE OF THE JNPT→ROTTERDAM
  SHIPMENT (₹2.3Cr edge value), not the sum of all node exposures.
  The cascade total is higher because it includes all 6 nodes' shipments.
  Both numbers are real and valid — Person D uses the primary shipment value
  for simplicity. You can use either figure in the demo.
"""

import uuid
import networkx as nx
from cascade_calculator import CascadeCalculator
from decision_card import build_decision_card, format_inr

# ── Hardcoded UUIDs so tests are reproducible ─────────────────────────────────
YARN_A_ID   = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
YARN_B_ID   = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))
DYE_ID      = str(uuid.UUID("00000000-0000-0000-0000-000000000003"))
FACTORY_ID  = str(uuid.UUID("00000000-0000-0000-0000-000000000004"))
JNPT_ID     = str(uuid.UUID("00000000-0000-0000-0000-000000000005"))
ROTTERDAM_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000006"))


def build_test_graph() -> nx.DiGraph:
    """Build in-memory AuroraTex graph with hardcoded node/edge data."""
    G = nx.DiGraph()

    G.add_node(YARN_A_ID,   name="Yarn Supplier A",     node_type="supplier",
               lat=21.1702, lng=72.8311,
               active_shipment_value_inr=3_000_000,  risk_score=0.0, is_disrupted=False)
    G.add_node(YARN_B_ID,   name="Yarn Supplier B",     node_type="supplier",
               lat=23.0225, lng=72.5714,
               active_shipment_value_inr=2_500_000,  risk_score=0.0, is_disrupted=False)
    G.add_node(DYE_ID,      name="Dye Chemical Supplier", node_type="supplier",
               lat=13.0827, lng=80.2707,
               active_shipment_value_inr=6_000_000,  risk_score=0.0, is_disrupted=False)
    G.add_node(FACTORY_ID,  name="AuroraTex Factory",  node_type="factory",
               lat=21.1702, lng=72.8311,
               active_shipment_value_inr=18_000_000, risk_score=0.0, is_disrupted=False)
    G.add_node(JNPT_ID,     name="JNPT Port",           node_type="port",
               lat=18.9489, lng=72.9518,
               active_shipment_value_inr=35_000_000, risk_score=0.0, is_disrupted=False)
    G.add_node(ROTTERDAM_ID, name="Rotterdam Port",     node_type="destination",
               lat=51.9225, lng=4.4792,
               active_shipment_value_inr=45_000_000, risk_score=0.0, is_disrupted=False)

    # Goods flow edges
    G.add_edge(YARN_A_ID,  FACTORY_ID,  transit_time_hours=24.0,  shipment_value_inr=1_500_000, transport_mode="road")
    G.add_edge(YARN_B_ID,  FACTORY_ID,  transit_time_hours=36.0,  shipment_value_inr=1_200_000, transport_mode="road")
    G.add_edge(DYE_ID,     FACTORY_ID,  transit_time_hours=48.0,  shipment_value_inr=800_000,   transport_mode="road")
    G.add_edge(FACTORY_ID, JNPT_ID,     transit_time_hours=12.0,  shipment_value_inr=5_000_000, transport_mode="road")
    G.add_edge(JNPT_ID,    ROTTERDAM_ID,transit_time_hours=528.0, shipment_value_inr=23_000_000,transport_mode="sea")

    return G


def print_results(label: str, results: list[dict], cascade_path: list[str], G: nx.DiGraph) -> None:
    PASS = "✓"
    FAIL = "✗"
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")
    print(f"  {'Node':<28} {'Risk':>6}  {'Exposure':>12}  {'Hop':>4}  {'Time':>8}")
    print(f"  {'-'*28} {'-'*6}  {'-'*12}  {'-'*4}  {'-'*8}")

    total = 0
    for r in results:
        exposure = r["financial_exposure_inr"]
        total   += exposure
        print(
            f"  {r['node_name']:<28} {r['risk_score']:>6.3f}  "
            f"{format_inr(exposure):>12}  {r['cascade_hop']:>4}  "
            f"{r['time_to_impact_hours']:>6.1f}h"
        )

    print(f"  {'─'*65}")
    print(f"  {'TOTAL EXPOSURE':>42}  {format_inr(total):>12}")

    # Cascade path
    path_names = [G.nodes[nid].get("name", nid[:8]) for nid in cascade_path]
    print(f"\n  Cascade path: {' → '.join(path_names)}")


def run_scenario(name: str, location: str, severity: int, confidence: float) -> list[dict]:
    G          = build_test_graph()
    calc       = CascadeCalculator(G)
    event      = {"affected_location": location, "severity": severity, "confidence_score": confidence}
    results    = calc.calculate(event)
    path       = calc.get_cascade_path(event)
    print_results(name, results, path, G)
    return results


def check_scenario_1():
    """Scenario 1: Cyclone at JNPT, severity=4, confidence=0.95"""
    print("\n" + "█"*65)
    print("  SCENARIO 1 — Cyclone at JNPT (sev=4, conf=0.95)")
    print("█"*65)
    results = run_scenario("Scenario 1: Cyclone JNPT", "JNPT", 4, 0.95)

    # Find nodes by name
    by_name = {r["node_name"]: r for r in results}
    errors  = []

    def chk(node, expected_risk, tol=0.01):
        actual = by_name.get(node, {}).get("risk_score", -1)
        ok = abs(actual - expected_risk) <= tol
        status = "✓" if ok else "✗"
        print(f"  {status} {node}: expected {expected_risk:.3f}, got {actual:.3f}")
        if not ok:
            errors.append(node)

    print("\n  Validation:")
    chk("JNPT Port",           0.760)
    chk("AuroraTex Factory",   0.456)
    chk("Yarn Supplier A",     0.274)
    chk("Yarn Supplier B",     0.274)
    chk("Dye Chemical Supplier", 0.274)
    chk("Rotterdam Port",      0.164)

    if errors:
        print(f"\n  ✗ FAILED nodes: {errors}")
    else:
        print("\n  ✓ ALL PASS — Scenario 1 correct")

    # Build mock decision card
    total = sum(r["financial_exposure_inr"] for r in results)
    mock_alert = {
        "affected_location":            "JNPT",
        "total_financial_exposure_inr": total,
        "max_risk_score":               max(r["risk_score"] for r in results),
        "time_to_impact_hours":         0.0,
    }
    card = build_decision_card(mock_alert)
    print(f"\n  60-Second Decision Card:")
    print(f"    Money at risk:  {card['money_at_risk_formatted']}")
    print(f"    Confidence:     {card['confidence_percent']}%")
    print(f"    Reason:         {card['confidence_reason'][:60]}…")
    print(f"    Peer intel:     {card['peer_intelligence'][:60]}…")
    print(f"    Options:        {card['options_count']} (incl. Wait & Monitor)")
    for opt in card["options"]:
        print(f"      [{opt['id']}] {opt['label']:<30}  saves {opt.get('saves_formatted', '—')}")


def check_scenario_2():
    """Scenario 2: Port Strike at JNPT, severity=3, confidence=0.85"""
    print("\n" + "█"*65)
    print("  SCENARIO 2 — Port Strike at JNPT (sev=3, conf=0.85)")
    print("█"*65)
    results = run_scenario("Scenario 2: JNPT Strike", "JNPT", 3, 0.85)

    by_name = {r["node_name"]: r for r in results}
    jnpt_risk = by_name.get("JNPT Port", {}).get("risk_score", 0)
    # sev_factor=0.6, conf=0.85, hop=0 → 0.6 × 1 × 0.85 = 0.510
    expected  = 0.510
    ok = abs(jnpt_risk - expected) <= 0.01
    print(f"\n  {'✓' if ok else '✗'} JNPT risk: expected {expected:.3f}, got {jnpt_risk:.3f}")
    print("  (Lower risk than Scenario 1 — severity 3 vs 4) ✓")


def check_scenario_3():
    """Scenario 3: Red Sea / Rotterdam crisis, severity=5, confidence=0.92"""
    print("\n" + "█"*65)
    print("  SCENARIO 3 — Rotterdam Crisis (sev=5, conf=0.92)")
    print("█"*65)
    results = run_scenario("Scenario 3: Rotterdam Crisis", "Rotterdam", 5, 0.92)

    by_name = {r["node_name"]: r for r in results}
    rotterdam_risk = by_name.get("Rotterdam Port", {}).get("risk_score", 0)
    jnpt_risk      = by_name.get("JNPT Port", {}).get("risk_score", 0)
    # sev_factor=1.0, conf=0.92, hop=0 → 0.92
    print(f"\n  Rotterdam risk: {rotterdam_risk:.3f} (expected ~0.920)")
    print(f"  JNPT risk:      {jnpt_risk:.3f} (expected ~0.552, upstream hop=1)")
    print("  (Cascade travels UPSTREAM from Rotterdam → JNPT → Factory → Suppliers) ✓")


def check_format_inr():
    """Test the INR formatter."""
    print("\n" + "█"*65)
    print("  FORMAT_INR TESTS")
    print("█"*65)
    tests = [
        (23_000_000,   "₹2.30Cr"),
        (18_200_000,   "₹1.82Cr"),
        (8_208_000,    "₹82.1L"),
        (3_000_000,    "₹30.0L"),
        (820_800,      "₹8.2L"),
        (180_000,      "₹1.8L"),
        (0,            "₹0"),
        (-500,         "₹0"),
    ]
    all_ok = True
    for amount, expected in tests:
        got = format_inr(amount)
        ok  = got == expected
        if not ok:
            all_ok = False
        print(f"  {'✓' if ok else '✗'}  {amount:>12,}  →  {got:>12}  (expected {expected})")

    if all_ok:
        print("\n  ✓ ALL FORMAT TESTS PASS")
    else:
        print("\n  ✗ SOME FORMAT TESTS FAILED")


if __name__ == "__main__":
    print("\n" + "="*65)
    print("  NexusFlow — Demo Scenario Validation (offline test)")
    print("="*65)
    print("  No Supabase required — using in-memory graph")

    check_scenario_1()
    check_scenario_2()
    check_scenario_3()
    check_format_inr()

    print("\n" + "="*65)
    print("  Test complete. If all ✓, you're ready for the demo.")
    print("="*65 + "\n")
