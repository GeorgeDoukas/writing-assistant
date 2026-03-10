import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import greeklish_to_greek, second_pass_corrections


class TestGreeklishToGreek(unittest.TestCase):
    # ----- single-character mappings -----
    def test_basic_vowels(self):
        self.assertEqual(greeklish_to_greek("a"), "α")
        self.assertEqual(greeklish_to_greek("e"), "ε")
        self.assertEqual(greeklish_to_greek("i"), "ι")
        self.assertEqual(greeklish_to_greek("o"), "ο")
        self.assertEqual(greeklish_to_greek("u"), "υ")

    def test_basic_consonants(self):
        self.assertEqual(greeklish_to_greek("b"), "β")
        self.assertEqual(greeklish_to_greek("d"), "δ")
        self.assertEqual(greeklish_to_greek("f"), "φ")
        self.assertEqual(greeklish_to_greek("g"), "γ")
        self.assertEqual(greeklish_to_greek("k"), "κ")
        self.assertEqual(greeklish_to_greek("l"), "λ")
        self.assertEqual(greeklish_to_greek("m"), "μ")
        self.assertEqual(greeklish_to_greek("n"), "ν")
        self.assertEqual(greeklish_to_greek("p"), "π")
        self.assertEqual(greeklish_to_greek("r"), "ρ")
        self.assertEqual(greeklish_to_greek("t"), "τ")
        self.assertEqual(greeklish_to_greek("v"), "β")
        self.assertEqual(greeklish_to_greek("w"), "ω")
        self.assertEqual(greeklish_to_greek("x"), "χ")  # x → χ directly
        self.assertEqual(greeklish_to_greek("z"), "ζ")

    def test_numeric_shortcuts(self):
        self.assertEqual(greeklish_to_greek("8"), "θ")   # 8 → θ
        self.assertEqual(greeklish_to_greek("3"), "ξ")   # 3 → ξ

    def test_question_mark_to_greek(self):
        self.assertEqual(greeklish_to_greek("?"), ";")   # ? → Greek question mark

    # ----- multi-character mappings -----
    def test_th(self):
        # 'th' is NOT a digraph in this style; maps to τ+η individually
        self.assertEqual(greeklish_to_greek("th"), "τη")

    def test_ps(self):
        self.assertEqual(greeklish_to_greek("ps"), "ψ")

    def test_ch(self):
        # 'ch' is NOT a digraph; c is not mapped, h → η
        result = greeklish_to_greek("ch")
        self.assertIn("η", result)
        self.assertNotEqual(result, "χ")  # ch ≠ χ; use x for χ

    def test_ks(self):
        # 'ks' is NOT a digraph; use '3' for ξ; trailing s becomes final sigma
        self.assertEqual(greeklish_to_greek("ks"), "κς")

    def test_ou(self):
        self.assertEqual(greeklish_to_greek("ou"), "ου")

    def test_mp(self):
        self.assertEqual(greeklish_to_greek("mp"), "μπ")

    def test_nt(self):
        self.assertEqual(greeklish_to_greek("nt"), "ντ")

    def test_gk(self):
        self.assertEqual(greeklish_to_greek("gk"), "γκ")

    def test_gg(self):
        self.assertEqual(greeklish_to_greek("gg"), "γγ")

    # ----- case preservation -----
    def test_uppercase_single(self):
        self.assertEqual(greeklish_to_greek("A"), "Α")
        self.assertEqual(greeklish_to_greek("K"), "Κ")

    def test_uppercase_multi(self):
        # TH is not a digraph; each letter converts independently
        self.assertEqual(greeklish_to_greek("TH"), "ΤΗ")
        self.assertEqual(greeklish_to_greek("PS"), "Ψ")

    def test_title_case_multi(self):
        result = greeklish_to_greek("Ps")
        self.assertEqual(result[0], result[0].upper())

    # ----- full words -----
    def test_word_kalimera(self):
        self.assertEqual(greeklish_to_greek("kalimera"), "καλιμερα")

    def test_word_with_th(self):
        # In this style, θ is typed as '8'; 'th' produces τη
        result = greeklish_to_greek("8alassa")
        self.assertIn("θ", result)

    def test_word_with_ou(self):
        result = greeklish_to_greek("koulouria")
        self.assertIn("ου", result)

    def test_word_sas(self):
        # final 's' must become final sigma ς
        result = greeklish_to_greek("sas")
        self.assertTrue(result.endswith("ς"), f"Expected final sigma, got: {result}")

    def test_word_kalos(self):
        result = greeklish_to_greek("kalos")
        self.assertEqual(result, "καλος")

    # ----- second pass: final sigma -----
    def test_final_sigma_end_of_string(self):
        result = second_pass_corrections("καλος")
        self.assertEqual(result, "καλος")  # 'ς' is already applied by greeklish_to_greek

    def test_final_sigma_before_punctuation(self):
        result = second_pass_corrections("καλοσ.")
        self.assertIn("ς", result)

    def test_final_sigma_mid_word_unchanged(self):
        result = second_pass_corrections("σαλάτα")
        self.assertTrue(result.startswith("σ"))

    # ----- passthrough characters -----
    def test_numbers_pass_through(self):
        # 1, 2 pass through; 3 → ξ and 8 → θ are special
        self.assertEqual(greeklish_to_greek("12"), "12")
        self.assertEqual(greeklish_to_greek("456790"), "456790")

    def test_punctuation_pass_through(self):
        # '?' maps to Greek question mark ';'
        self.assertEqual(greeklish_to_greek("!.,"), "!.,")
        self.assertEqual(greeklish_to_greek("?"), ";")
        self.assertEqual(greeklish_to_greek("!?.,"), "!;.,")

    def test_spaces_preserved(self):
        result = greeklish_to_greek("a b")
        self.assertEqual(result, "α β")

    def test_mixed_greek_english_passthrough(self):
        # Already-Greek characters pass through unchanged
        result = greeklish_to_greek("αβγ")
        self.assertEqual(result, "αβγ")

    # ----- sentences -----
    def test_sentence(self):
        result = greeklish_to_greek("geia sas")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_empty_string(self):
        self.assertEqual(greeklish_to_greek(""), "")

    def test_multiline(self):
        result = greeklish_to_greek("geia\nsas")
        self.assertIn("\n", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
