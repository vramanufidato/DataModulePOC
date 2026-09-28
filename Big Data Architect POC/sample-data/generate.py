"""
Generate reproducible sample data for the multi-cloud data platform POC.

Produces:
  - orders.json     (JSON Lines, 10K records)
  - customers.csv   (2K records)
  - products.parquet (50 records)

Deterministic via Faker + random seed from config.yaml.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from faker import Faker

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open() as fh:
        return yaml.safe_load(fh)


def seed_everything(seed: int) -> Faker:
    random.seed(seed)
    fake = Faker()
    Faker.seed(seed)
    return fake


def generate_orders(cfg: dict[str, Any], fake: Faker) -> list[dict[str, Any]]:
    o = cfg["orders"]
    start = datetime.fromisoformat(o["start_date"].replace("Z", "+00:00"))

    rows: list[dict[str, Any]] = []
    for i in range(o["count"]):
        qty = random.randint(1, 5)
        price = random.choice(o["price_points"])
        order_ts = start + timedelta(minutes=i * o["increment_minutes"])

        rows.append(
            {
                "order_id": f"ORD-{100000 + i + 1}",
                "customer_id": f"CUST-{random.randint(o['customer_id_range']['min'], o['customer_id_range']['max'])}",
                "product_id": f"PROD-{random.randint(o['product_id_range']['min'], o['product_id_range']['max'])}",
                "quantity": qty,
                "amount": round(qty * price, 2),
                "currency": "USD",
                "order_ts": order_ts.isoformat().replace("+00:00", "Z"),
                "region": random.choice(o["regions"]),
                "channel": random.choice(o["channels"]),
                "status": random.choice(o["statuses"]),
            }
        )
    return rows


def generate_customers(cfg: dict[str, Any], fake: Faker) -> pd.DataFrame:
    c = cfg["customers"]
    start = datetime(2026, 9, 1)

    rows = []
    for i in range(c["count"]):
        signup = start - timedelta(days=random.randint(0, c["signup_lookback_days"]))
        rows.append(
            {
                "customer_id": f"CUST-{c['id_start'] + i}",
                "name": fake.name(),
                "email": fake.email(),
                "region": random.choice(c["regions"]),
                "signup_date": signup.date().isoformat(),
                "tier": random.choice(c["tiers"]),
            }
        )
    return pd.DataFrame(rows)


def generate_products(cfg: dict[str, Any], fake: Faker) -> pd.DataFrame:
    p = cfg["products"]

    rows = []
    for i in range(p["count"]):
        rows.append(
            {
                "product_id": f"PROD-{p['id_start'] + i}",
                "name": fake.catch_phrase(),
                "category": random.choice(p["categories"]),
                "brand": fake.company(),
                "unit_price": round(
                    random.uniform(p["unit_price_range"]["min"], p["unit_price_range"]["max"]), 2
                ),
            }
        )
    return pd.DataFrame(rows)


def write_outputs(
    out_dir: Path,
    orders: list[dict[str, Any]],
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    orders_path = out_dir / "orders.json"
    with orders_path.open("w") as fh:
        for row in orders:
            fh.write(json.dumps(row) + "\n")

    customers.to_csv(out_dir / "customers.csv", index=False)
    products.to_parquet(out_dir / "products.parquet", index=False)

    print(f"[OK] orders.json     ({len(orders):>6} rows) -> {orders_path}")
    print(f"[OK] customers.csv   ({len(customers):>6} rows) -> {out_dir / 'customers.csv'}")
    print(f"[OK] products.parquet ({len(products):>6} rows) -> {out_dir / 'products.parquet'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate POC sample data")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--seed", type=int, default=None, help="Override seed from config")
    parser.add_argument("--out", type=Path, default=None, help="Override output dir")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    if args.seed is not None:
        cfg["seed"] = args.seed

    out_dir = args.out or Path(__file__).parent / cfg["output_dir"]
    fake = seed_everything(cfg["seed"])

    print(f"Generating data (seed={cfg['seed']}) -> {out_dir}")
    orders = generate_orders(cfg, fake)
    customers = generate_customers(cfg, fake)
    products = generate_products(cfg, fake)

    write_outputs(out_dir, orders, customers, products)
    return 0


if __name__ == "__main__":
    sys.exit(main())
