"""
Transliteration variant generator.

Applies a set of "optional" phonetic/orthographic rules to an input word
and generates ALL possible surface-form variants (every optional rule can
either fire or not, combinatorially), then prints up to `max_outputs`
of them.

Usage:
    python translit.py masala
    python translit.py masala --max 50
"""

import argparse
import itertools
import re
import unicodedata


# ---------------------------------------------------------------------------
# Step 1: accent / diacritic removal (mandatory, always applied first)
# ---------------------------------------------------------------------------

def remove_accents(text: str) -> str:
    """Strip combining diacritical marks (NFD decompose, drop combining chars)."""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


# ---------------------------------------------------------------------------
# Step 2: n̐ / m̐ -> n  (mandatory, done on the accented string before strip,
#          since accent removal would otherwise just drop the tilde and
#          leave n/m unchanged anyway -- but we special-case to be safe)
# ---------------------------------------------------------------------------

def normalize_tilde_nasals(text: str) -> str:
    # handle n̐ and m̐ (n or m followed by combining tilde U+0310, or the
    # precomposed look using U+0303 combining tilde as well, just in case)
    text = re.sub(r"[nm]\u0303", "n", text)
    text = re.sub(r"[nm]\u0310", "n", text)
    return text


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
#
# Each rule is a function: (word: str) -> list[str]
# It receives the current word and returns the list of possible
# replacements for that whole word after considering the rule at every
# place it applies, INCLUDING the "rule not applied" (original) option
# when the rule is optional.
#
# To keep the combinatorics manageable and correct, we implement each
# rule as a function that takes a single string and returns a SET of
# possible output strings (branching only at the places the pattern
# actually matches). We then chain rules: after each rule runs, the
# working set of candidate strings grows (or stays the same if the
# pattern never matched).


def apply_pattern_branch(words: set, pattern: str, build_variants, flags=0):
    """
    For each word in `words`, find all matches of `pattern`. For every
    match, branch into (a) leaving it unchanged, and (b) each replacement
    provided by build_variants(match). This is applied so that ALL
    matches in the string are independently branched (combinatorial).

    build_variants(match_obj) -> list[str]  (replacement strings for
    that match; the "keep original" option is added automatically)
    """
    result = set()

    for word in words:
        regex = re.compile(pattern, flags)
        matches = list(regex.finditer(word))

        if not matches:
            result.add(word)
            continue

        # For each match, the set of choices is: [original_matched_text] + variants
        choice_lists = []
        for m in matches:
            variants = build_variants(m)
            options = [m.group(0)] + [v for v in variants if v != m.group(0)]
            # dedupe while preserving order
            seen = set()
            uniq = []
            for o in options:
                if o not in seen:
                    seen.add(o)
                    uniq.append(o)
            choice_lists.append(uniq)

        # Build all combinations of choices across all match positions
        for combo in itertools.product(*choice_lists):
            pieces = []
            last_end = 0
            for m, chosen in zip(matches, combo):
                pieces.append(word[last_end:m.start()])
                pieces.append(chosen)
                last_end = m.end()
            pieces.append(word[last_end:])
            result.add("".join(pieces))

    return result


# ---- Individual rule definitions -------------------------------------------

def rule_ng_a(words):
    # ṅa -> nga  (after accent removal ṅ -> n, so original "ṅa" is "na";
    # but to distinguish from plain "na" we must run this BEFORE accent
    # stripping in the pipeline; see main pipeline ordering)
    return apply_pattern_branch(words, r"\u1e45a", lambda m: ["nga"])


def rule_b(words):
    # b -> v (can also be b)  => optional
    return apply_pattern_branch(words, r"b", lambda m: ["v"])


def rule_bh(words):
    # bh -> v (or bh)
    return apply_pattern_branch(words, r"bh", lambda m: ["v"])


def rule_sha_from_sh(words):
    # śa -> sha  (ś handled pre-accent-strip; see pipeline)
    return apply_pattern_branch(words, r"\u015ba", lambda m: ["sha"])


def rule_sa_to_sha(words):
    # sa -> sha
    return apply_pattern_branch(words, r"sa", lambda m: ["sha"])


def rule_anusvara(words):
    # ṃ -> ng
    return apply_pattern_branch(words, r"\u1e43", lambda m: ["ng"])


def rule_ya_to_ja(words):
    # ya -> ja
    return apply_pattern_branch(words, r"ya", lambda m: ["ja"])


def rule_ẏa_to_ya(words):
    # ẏa -> ya  (ẏ = y with dot above, U+1E8F)
    return apply_pattern_branch(words, r"\u1e8fa", lambda m: ["ya"])


def rule_ca_to_cha(words):
    # ca -> cha
    return apply_pattern_branch(words, r"ca", lambda m: ["cha"])


def rule_cha_to_chha(words):
    # cha -> chha (or cha)
    return apply_pattern_branch(words, r"cha", lambda m: ["chha"])


def rule_cch(words):
    # cch -> ch / chchh / chh / chch  (e.g. hochhe)
    return apply_pattern_branch(
        words, r"cch", lambda m: ["ch", "chchh", "chh", "chch"]
    )


def rule_cc(words):
    # cc -> chch / cch (e.g. bachcha)
    return apply_pattern_branch(words, r"cc", lambda m: ["chch", "cch"])


def rule_visarga(words):
    # ḥ -> delete it and double the following consonant
    # duḥkha -> dukkha (then a-deletion rule elsewhere gives dukkho etc.)
    consonant = r"[bcdfghjklmnpqrstvwxyzḍṭṇṛśṣñṅ]"

    def build(m):
        following = m.group(1)
        return [following + following]

    return apply_pattern_branch(
        words, r"\u1e25(" + consonant + ")", build, flags=re.IGNORECASE
    )


def rule_ya_after_consonant(words):
    # ya after a consonant sound (excluding h) -> delete "y", double the
    # consonant.  bakya -> bakko  (b-a-k-ya -> bakka -> ...)
    # We match: (consonant, not h)(y)a
    consonant_not_h = r"[bcdfgjklmnpqrstvwxzḍṭṇṛśṣñṅ]"

    def build(m):
        cons = m.group(1)
        return [cons + cons + "a"]

    return apply_pattern_branch(
        words, r"(" + consonant_not_h + r")ya", build
    )


def rule_ya_after_h(words):
    # ya after h -> hya / haa
    return apply_pattern_branch(words, r"hya", lambda m: ["hya", "haa"])


def rule_au(words):
    return apply_pattern_branch(words, r"au", lambda m: ["ou"])


def rule_ai(words):
    return apply_pattern_branch(words, r"ai", lambda m: ["oi"])


def rule_a_delete(words):
    # a -> nothing (optional deletion of bare 'a')
    return apply_pattern_branch(words, r"a", lambda m: [""])


def rule_a_to_o(words):
    # a -> o (optional)
    return apply_pattern_branch(words, r"a", lambda m: ["o"])


def rule_v_to_b_bh(words):
    # v -> b / bh
    return apply_pattern_branch(words, r"v", lambda m: ["b", "bh"])


def rule_ṛ_to_ri(words):
    # r̥ -> ri  (r + combining ring below, U+0325) -- run pre accent-strip
    return apply_pattern_branch(words, r"r\u0325", lambda m: ["ri"])


def rule_ṛha(words):
    # ṛha -> rha / ra   (ṛ = U+1E5B)
    return apply_pattern_branch(words, r"\u1e5bha", lambda m: ["rha", "ra"])


def rule_i_macron(words):
    # ī -> i / ee  (ī = U+012B) -- run pre accent-strip
    return apply_pattern_branch(words, r"\u012b", lambda m: ["i", "ee"])


def rule_e(words):
    # e -> a
    return apply_pattern_branch(words, r"e", lambda m: ["a"])


def rule_a_macron(words):
    # ā -> aa / a  (ā = U+0101) -- run pre accent-strip
    return apply_pattern_branch(words, r"\u0101", lambda m: ["aa", "a"])


def rule_aa_to_a(words):
    # aa -> a, but NOT when it would produce/represent "o" context.
    # Interpreted literally: aa -> a is allowed generally; guard against
    # collapsing into rule_a_to_o's "o" output (i.e. don't chain aa->a->o
    # in a way that conflicts). We simply add "a" as an alternative to "aa".
    return apply_pattern_branch(words, r"aa", lambda m: ["a"])


def rule_sh_b_delete(words):
    # "B after sh" -> becomes nothing. Interpreted as: sh + b -> sh
    return apply_pattern_branch(words, r"shb", lambda m: ["sh"])


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
#
# Ordering matters. Rules that depend on specific diacritics (ṅ, ś, ṃ, ẏ,
# ḥ, r̥, ṛ, ī, ā) must run BEFORE accent removal, since accent removal
# would strip those diacritics and make the patterns unmatchable.
# Rules like cch/cc must run before the single-c related rules to avoid
# double-processing. ya-after-consonant / ya-after-h must run before the
# generic ya->ja rule. aa-related rules run after ā is resolved.

def generate_variants(word: str, max_outputs: int = 25):
    words = {word}

    # --- Diacritic-dependent rules (run before stripping accents) ---
    words = rule_ng_a(words)          # ṅa -> nga
    words = rule_sha_from_sh(words)   # śa -> sha
    words = rule_anusvara(words)      # ṃ -> ng
    words = rule_ẏa_to_ya(words)      # ẏa -> ya
    words = rule_visarga(words)       # ḥ + consonant -> double consonant
    words = rule_ṛha(words)           # ṛha -> rha / ra
    words = rule_ṛ_to_ri(words)       # r̥ -> ri
    words = rule_i_macron(words)      # ī -> i / ee
    words = rule_a_macron(words)      # ā -> aa / a

    # --- Now strip any remaining accents/diacritics + tilde nasals ---
    words = {normalize_tilde_nasals(w) for w in words}
    words = {remove_accents(w) for w in words}

    # --- Digraph / cluster rules (before single-letter rules that could
    #     interfere) ---
    words = rule_cch(words)           # cch -> ch/chchh/chh/chch
    words = rule_cc(words)            # cc -> chch/cch
    words = rule_cha_to_chha(words)   # cha -> chha (or cha)
    words = rule_ca_to_cha(words)     # ca -> cha

    words = rule_ya_after_h(words)    # hya -> hya/haa
    words = rule_ya_after_consonant(words)  # (cons)ya -> double cons
    words = rule_ya_to_ja(words)      # ya -> ja

    words = rule_sa_to_sha(words)     # sa -> sha
    words = rule_bh(words)            # bh -> v (or bh)
    words = rule_b(words)             # b -> v (can also be b)
    words = rule_v_to_b_bh(words)     # v -> b / bh

    words = rule_au(words)            # au -> ou
    words = rule_ai(words)            # ai -> oi
    words = rule_e(words)             # e -> a

    words = rule_aa_to_a(words)       # aa -> a
    words = rule_a_to_o(words)        # a -> o
    words = rule_a_delete(words)      # a -> nothing

    words = rule_sh_b_delete(words)   # shb -> sh

    # final cleanup: drop empties / dedupe
    words = {w for w in words if w}

    ordered = sorted(words, key=lambda w: (len(w), w))
    return ordered[:max_outputs], len(words)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate transliteration variants.")
    parser.add_argument("word", help="Input word (IAST/diacritic transliteration)")
    parser.add_argument(
        "--max", type=int, default=25, dest="max_outputs",
        help="Maximum number of variants to print (default: 25)"
    )
    args = parser.parse_args()

    variants, total = generate_variants(args.word, args.max_outputs)

    print(f"Input: {args.word}")
    print(f"Total unique variants generated: {total}")
    print(f"Showing: {len(variants)}\n")
    for v in variants:
        print(v)


if __name__ == "__main__":
    main()