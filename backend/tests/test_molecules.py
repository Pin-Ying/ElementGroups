"""分子資料的正規化。

這裡測的是後端這一半：從分子式解析元素、產生網址代稱。前端那一半
（依金屬性分類）在 frontend/src/utils/moleculeCategory.test.js。

兩邊要對得起來——後端 elements_in_formula() 吐出的元素清單，正是前端
autoCategory() 拿去判定分類的輸入。這裡的案例刻意用同一組分子。
"""

import pytest

from conftest import load_app_module

molecules = load_app_module("molecules")


class TestElementsInFormula:
    """從分子式取出用到的元素符號，供分子與元素頁互相連結。"""

    @pytest.mark.parametrize("formula,expected", [
        ("H2O", ["H", "O"]),
        ("N2", ["N"]),
        ("ClNa", ["Cl", "Na"]),        # PubChem 的排序，不是習慣的 NaCl
        ("CaCO3", ["Ca", "C", "O"]),
        ("C2H6O", ["C", "H", "O"]),
        ("SiO2", ["Si", "O"]),
    ])
    def test_common_formulas(self, formula, expected):
        assert molecules.elements_in_formula(formula) == expected

    def test_two_letter_symbols_not_split(self):
        """Cl 要當成一個元素，不能拆成 C 和 l。
        大小寫規則就是唯一的線索，這也是為什麼元素符號一定是首字大寫。"""
        assert molecules.elements_in_formula("Cl2") == ["Cl"]
        assert molecules.elements_in_formula("NaCl") == ["Na", "Cl"]

    def test_deduplicated_and_ordered(self):
        """重複的只留第一次出現，順序照分子式。"""
        assert molecules.elements_in_formula("CH3COOH") == ["C", "H", "O"]

    @pytest.mark.parametrize("bad", ["", None, "123", "()"])
    def test_no_elements(self, bad):
        assert molecules.elements_in_formula(bad) == []


class TestNormalizeSlug:
    """IUPAC 名稱轉網址代稱。"""

    def test_lowercase_and_hyphenate(self):
        assert molecules.normalize_slug("Sodium Chloride") == "sodium-chloride"

    def test_strips_brackets(self):
        """IUPAC 名稱常含括號、逗號與上標，一併清掉。"""
        assert molecules.normalize_slug("(2R)-butan-2-ol") == "2r-butan-2-ol"
        assert molecules.normalize_slug("benzene[a]pyrene") == "benzene-a-pyrene"

    def test_collapses_separators(self):
        assert molecules.normalize_slug("a,,,b") == "a-b"
        assert molecules.normalize_slug("  spaced   out  ") == "spaced-out"

    def test_returns_none_when_nothing_usable(self):
        """產不出合法 slug 時回 None，呼叫端據此請使用者改用英文名稱。"""
        assert molecules.normalize_slug("") is None
        assert molecules.normalize_slug(None) is None
        assert molecules.normalize_slug("中文名稱") is None
        assert molecules.normalize_slug("---") is None

    def test_length_cap(self):
        assert len(molecules.normalize_slug("a" * 200)) == 80


class TestNormalizeMolecule:
    def test_fills_elements_from_formula_when_absent(self):
        """舊資料沒有 elements 欄位時，從分子式補上——
        前端的分類完全依賴這個欄位，缺了會變成「其他」。"""
        m = molecules.normalize_molecule("oxidane", {"formula": "H2O"})
        assert m["elements"] == ["H", "O"]

    def test_keeps_existing_elements(self):
        m = molecules.normalize_molecule("x", {"formula": "H2O", "elements": ["H"]})
        assert m["elements"] == ["H"]

    def test_name_falls_back_to_slug(self):
        assert molecules.normalize_molecule("water", {})["name"] == "water"

    def test_published_defaults_true(self):
        assert molecules.normalize_molecule("x", {})["published"] is True

    def test_rejects_non_dict(self):
        assert molecules.normalize_molecule("x", None) is None
        assert molecules.normalize_molecule("x", "not a dict") is None


class TestNormalizeMolecules:
    def test_drafts_hidden_by_default(self):
        data = {
            "a": {"formula": "H2O", "published": True},
            "b": {"formula": "N2", "published": False},
        }
        assert [m["slug"] for m in molecules.normalize_molecules(data)] == ["a"]
        assert len(molecules.normalize_molecules(data, include_drafts=True)) == 2

    def test_sorted_by_updated_at_desc(self):
        data = {
            "old": {"formula": "N2", "updated_at": "2026-01-01T00:00:00Z"},
            "new": {"formula": "O2", "updated_at": "2026-09-01T00:00:00Z"},
            "none": {"formula": "H2"},
        }
        order = [m["slug"] for m in molecules.normalize_molecules(data)]
        assert order[0] == "new"
        assert order[-1] == "none"   # 沒有時間戳的排最後
