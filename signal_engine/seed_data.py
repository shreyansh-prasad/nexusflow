"""
seed_data.py — Insert AuroraTex supply chain graph into Supabase.

Run ONCE on Day 1:
  python seed_data.py

Safe to re-run — checks for existing data before inserting.
To re-seed from scratch, run this SQL in Supabase SQL Editor first:
  DELETE FROM supply_chain_edges WHERE company_id = 'auroratea';
  DELETE FROM supply_chain_nodes WHERE company_id = 'auroratea';
Then run seed_data.py again.
"""

import logging
import sys
from db import supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

COMPANY_ID = "auroratea"


def is_already_seeded() -> bool:
    """Return True if AuroraTex nodes already exist in DB."""
    result = supabase.table("supply_chain_nodes") \
        .select("id") \
        .eq("company_id", COMPANY_ID) \
        .execute()
    return len(result.data or []) > 0


def seed_nodes() -> dict[str, str]:
    """
    Insert 6 AuroraTex supply chain nodes.
    Returns dict: node_name → UUID (needed to build edges).
    """
    nodes = [
        {
            "company_id":                COMPANY_ID,
            "name":                      "Yarn Supplier A",
            "node_type":                 "supplier",
            "lat":                       21.1702,
            "lng":                       72.8311,
            "total_inventory_value_inr": 5_000_000,   # ₹50L
            "active_shipment_value_inr": 3_000_000,   # ₹30L
        },
        {
            "company_id":                COMPANY_ID,
            "name":                      "Yarn Supplier B",
            "node_type":                 "supplier",
            "lat":                       23.0225,
            "lng":                       72.5714,
            "total_inventory_value_inr": 4_000_000,   # ₹40L
            "active_shipment_value_inr": 2_500_000,   # ₹25L
        },
        {
            "company_id":                COMPANY_ID,
            "name":                      "Dye Chemical Supplier",
            "node_type":                 "supplier",
            "lat":                       13.0827,
            "lng":                       80.2707,
            "total_inventory_value_inr": 8_000_000,   # ₹80L
            "active_shipment_value_inr": 6_000_000,   # ₹60L
        },
        {
            "company_id":                COMPANY_ID,
            "name":                      "AuroraTex Factory",
            "node_type":                 "factory",
            "lat":                       21.1702,
            "lng":                       72.8311,
            "total_inventory_value_inr": 25_000_000,  # ₹2.5Cr
            "active_shipment_value_inr": 18_000_000,  # ₹1.8Cr
        },
        {
            "company_id":                COMPANY_ID,
            "name":                      "JNPT Port",
            "node_type":                 "port",
            "lat":                       18.9489,
            "lng":                       72.9518,
            "total_inventory_value_inr": 50_000_000,  # ₹5Cr
            "active_shipment_value_inr": 35_000_000,  # ₹3.5Cr
        },
        {
            "company_id":                COMPANY_ID,
            "name":                      "Rotterdam Port",
            "node_type":                 "destination",
            "lat":                       51.9225,
            "lng":                       4.4792,
            "total_inventory_value_inr": 60_000_000,  # ₹6Cr
            "active_shipment_value_inr": 45_000_000,  # ₹4.5Cr
        },
    ]

    result = supabase.table("supply_chain_nodes").insert(nodes).execute()
    if not result.data:
        raise RuntimeError("Node insertion returned empty data — check Supabase logs")

    name_to_id = {row["name"]: row["id"] for row in result.data}
    logger.info(f"  Inserted {len(name_to_id)} nodes:")
    for name, uid in name_to_id.items():
        logger.info(f"    {name:30} → {uid}")
    return name_to_id


def seed_edges(name_to_id: dict[str, str]) -> None:
    """
    Insert 5 AuroraTex supply chain edges.
    Edge direction = direction of goods flow (source → target).
    """
    required = [
        "Yarn Supplier A", "Yarn Supplier B", "Dye Chemical Supplier",
        "AuroraTex Factory", "JNPT Port", "Rotterdam Port",
    ]
    missing = [n for n in required if n not in name_to_id]
    if missing:
        raise ValueError(f"Missing node IDs for: {missing}")

    edges = [
        # Yarn Supplier A → AuroraTex Factory (road, 1 day, ₹15L)
        {
            "company_id":         COMPANY_ID,
            "source_node_id":     name_to_id["Yarn Supplier A"],
            "target_node_id":     name_to_id["AuroraTex Factory"],
            "transit_time_days":  1.0,
            "shipment_value_inr": 1_500_000,
            "transport_mode":     "road",
        },
        # Yarn Supplier B → AuroraTex Factory (road, 1.5 days, ₹12L)
        {
            "company_id":         COMPANY_ID,
            "source_node_id":     name_to_id["Yarn Supplier B"],
            "target_node_id":     name_to_id["AuroraTex Factory"],
            "transit_time_days":  1.5,
            "shipment_value_inr": 1_200_000,
            "transport_mode":     "road",
        },
        # Dye Chemical Supplier → AuroraTex Factory (road, 2 days, ₹8L)
        {
            "company_id":         COMPANY_ID,
            "source_node_id":     name_to_id["Dye Chemical Supplier"],
            "target_node_id":     name_to_id["AuroraTex Factory"],
            "transit_time_days":  2.0,
            "shipment_value_inr": 800_000,
            "transport_mode":     "road",
        },
        # AuroraTex Factory → JNPT Port (road, 0.5 days, ₹50L)
        {
            "company_id":         COMPANY_ID,
            "source_node_id":     name_to_id["AuroraTex Factory"],
            "target_node_id":     name_to_id["JNPT Port"],
            "transit_time_days":  0.5,
            "shipment_value_inr": 5_000_000,
            "transport_mode":     "road",
        },
        # JNPT Port → Rotterdam Port (sea, 22 days, ₹2.3Cr)
        {
            "company_id":         COMPANY_ID,
            "source_node_id":     name_to_id["JNPT Port"],
            "target_node_id":     name_to_id["Rotterdam Port"],
            "transit_time_days":  22.0,
            "shipment_value_inr": 23_000_000,
            "transport_mode":     "sea",
        },
    ]

    result = supabase.table("supply_chain_edges").insert(edges).execute()
    if not result.data:
        raise RuntimeError("Edge insertion returned empty data — check Supabase logs")

    logger.info(f"  Inserted {len(result.data)} edges ✓")


def main():
    logger.info("=" * 60)
    logger.info("  NexusFlow — AuroraTex Seed Data")
    logger.info("=" * 60)

    if is_already_seeded():
        logger.warning("Data already exists for 'auroratea'. Skipping.")
        logger.warning(
            "To re-seed: DELETE edges and nodes in Supabase SQL Editor, then re-run."
        )
        sys.exit(0)

    logger.info("Seeding nodes…")
    try:
        name_to_id = seed_nodes()
    except Exception as exc:
        logger.error(f"Node seeding failed: {exc}")
        sys.exit(1)

    logger.info("Seeding edges…")
    try:
        seed_edges(name_to_id)
    except Exception as exc:
        logger.error(f"Edge seeding failed: {exc}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("  ✓ Seed complete! AuroraTex graph is ready.")
    logger.info("  Verify with:")
    logger.info("    python -c \"from graph_builder import *; print_graph_summary(build_graph())\"")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
