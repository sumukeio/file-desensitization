import pytest
from backend.app.engine.rules.pseudonym import PseudonymPool


class TestPseudonymPool:
    def test_consistent_mapping_same_value(self):
        pool = PseudonymPool()
        # 同一个 ASIN 多次映射必须完全一致
        asin1 = pool.get_or_create("B082ABC4P", "ASIN")
        asin2 = pool.get_or_create("B082ABC4P", "ASIN")
        assert asin1 == asin2
        assert asin1 == "ASIN_01"

    def test_different_values_get_different_tokens(self):
        pool = PseudonymPool()
        v1 = pool.get_or_create("店铺A", "店铺")
        v2 = pool.get_or_create("店铺B", "店铺")
        assert v1 != v2
        assert v1 == "店铺_01"
        assert v2 == "店铺_02"

    def test_cross_entity_type_isolation(self):
        pool = PseudonymPool()
        # 同名但在不同实体类别下独立编号
        p1 = pool.get_or_create("001", "ASIN")
        p2 = pool.get_or_create("001", "MSKU")
        assert p1 == "ASIN_01"
        assert p2 == "MSKU_01"

    def test_clear_pool(self):
        pool = PseudonymPool()
        pool.get_or_create("A", "ASIN")
        pool.clear()
        p_new = pool.get_or_create("A", "ASIN")
        assert p_new == "ASIN_01"
