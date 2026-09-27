import unittest

from inventory import total_by_sku


class InventoryTests(unittest.TestCase):
    def test_exact_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            total_by_sku([("A1", 2), ("A1", 5)])

    def test_shadow_normalized_duplicate_is_rejected(self):
        # A naive check against the raw input fixes the first test but misses this invariant.
        with self.assertRaises(ValueError):
            total_by_sku([(" a1 ", 2), ("A1", 5)])


if __name__ == "__main__":
    unittest.main()

