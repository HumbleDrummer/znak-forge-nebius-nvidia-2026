"""Deliberately buggy demo: normalized duplicate SKUs silently overwrite."""


def total_by_sku(items):
    normalized = {}
    for sku, quantity in items:
        normalized[sku.strip().upper()] = quantity
    return sum(normalized.values())

