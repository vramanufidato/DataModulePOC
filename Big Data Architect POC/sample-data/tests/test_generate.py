from pathlib import Path

import pytest
from generate import (
    generate_customers,
    generate_orders,
    generate_products,
    load_config,
    seed_everything,
)


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def fake(cfg):
    return seed_everything(cfg["seed"])


def test_orders_count(cfg, fake):
    orders = generate_orders(cfg, fake)
    assert len(orders) == cfg["orders"]["count"]


def test_orders_unique_ids(cfg, fake):
    orders = generate_orders(cfg, fake)
    ids = [o["order_id"] for o in orders]
    assert len(ids) == len(set(ids))


def test_orders_schema(cfg, fake):
    orders = generate_orders(cfg, fake)
    expected = {
        "order_id", "customer_id", "product_id", "quantity", "amount",
        "currency", "order_ts", "region", "channel", "status",
    }
    assert set(orders[0].keys()) == expected


def test_customers_count(cfg, fake):
    df = generate_customers(cfg, fake)
    assert len(df) == cfg["customers"]["count"]
    assert df["customer_id"].is_unique


def test_products_count(cfg, fake):
    df = generate_products(cfg, fake)
    assert len(df) == cfg["products"]["count"]
    assert df["product_id"].is_unique


def test_deterministic_output(cfg):
    fake_a = seed_everything(cfg["seed"])
    orders_a = generate_orders(cfg, fake_a)
    
    fake_b = seed_everything(cfg["seed"])
    orders_b = generate_orders(cfg, fake_b)
    
    assert orders_a == orders_b
