"""Builds app/assets/dict.tsv for the keyboard's suggestions.

Words and frequencies come from wordfreq (German "large" list plus the most
common English words, weighted lower); wordfreq lowercases everything, so the
German spelling of nouns (Haus, Häuser) is taken from the igerman98 hunspell
dictionary. Nothing is filtered out: slang and swear words stay in.

Output, sorted by the lowercase key: key <TAB> display form <TAB> zipf*100
"""

import os
import re
import sys

import wordfreq

DE_WORDS, EN_WORDS = 90000, 20000
EN_PENALTY = 1.2          # English words rank below German ones of the same frequency
WORD = re.compile(r"^[a-zäöüßàâçéèêëîïôûùüÿñæœ'-]+$")
SUFFIXES = ["nen", "ern", "en", "er", "es", "n", "s", "e"]
SZ_FIXED = {"ausser": "außer", "ausserdem": "außerdem", "aussen": "außen", "draussen": "draußen"}
SZ_AFTER = ("eiss", "iess", "euss", "äuss")   # ß after ei/ie/eu/äu (heiß, ließ, scheiß)
VERB_ENDINGS = ["e", "st", "t", "te", "ten", "test", "tet", "et", "est", "end", "ete", "eten"]
ADJ_ENDINGS = ["e", "en", "er", "es", "em", "ere", "eren", "erer", "eres", "erem", "ste", "sten", "ster", "stes", "stem"]
FORCE_LOWER = {"hab", "halt", "schau", "sag", "mach", "komm", "geh", "guck", "lass", "hör", "bleib", "wart", "ruf"}
TYPO_GAP = 1.5            # a rare unknown word with two letters swapped from one 30x more common is a typo (nciht)


def hunspell_case(dic_path):
    standalone_lower, capitalized, any_lower = set(), {}, set()
    global ALL_LOWER, SS_TO_SZ, SZ_WORDS, VERBS, ADJS
    ALL_LOWER, SS_TO_SZ, SZ_WORDS, VERBS, ADJS = set(), {}, set(), set(), set()
    with open(dic_path, encoding="utf-8") as f:
        next(f)
        for line in f:
            line = line.strip()
            if not line or line.startswith(("\t", "#")):
                continue
            word, _, flags = line.partition("/")
            low = word.lower()
            ALL_LOWER.add(low)
            if "ß" in low:
                SS_TO_SZ.setdefault(low.replace("ß", "ss"), low)
                SZ_WORDS.add(low)
            if word[:1].isupper():
                capitalized.setdefault(low, word)
            else:
                any_lower.add(low)
                if "D" in flags and low.endswith("n"):
                    VERBS.add(low)
                if "A" in flags:
                    ADJS.add(low)
                if "o" not in flags and "h" not in flags:   # o = only in compounds, h = needs an affix
                    standalone_lower.add(low)
    return standalone_lower, capitalized, any_lower


def restore_sz(w):
    """wordfreq casefolds ß to ss; bring it back where the dictionary says so."""
    if "ss" not in w or w in ALL_LOWER:
        return w
    if w in SS_TO_SZ:
        return SS_TO_SZ[w]
    if w in SZ_FIXED:
        return SZ_FIXED[w]
    for pat in SZ_AFTER:
        if pat in w:
            return w.replace(pat, pat[:-2] + "ß")
    i = w.find("ss")
    while i >= 0:                     # größer: some ß word ("groß") must start the candidate
        cand = w[:i] + "ß" + w[i + 2:]
        if any(cand[:n] in SZ_WORDS for n in range(i + 1, len(cand) + 1)) or any(
                z.startswith(cand[: i + 1]) for z in SZ_WORDS if len(cand) > i + 1):   # grüße <- grüßen
            return cand
        i = w.find("ss", i + 1)
    return w


def also_lowercase(w):
    """Verb or adjective forms that are also nouns (macht/Macht, bitte/Bitte, alten/Alten)."""
    if w in FORCE_LOWER:
        return True
    for suf in VERB_ENDINGS:
        stem = w[: -len(suf)]
        if w.endswith(suf) and len(stem) >= 2 and (suf[0] == "e" or stem[-1] not in "td") and (
                stem + "en" in VERBS or (stem[-1] in "lr" and stem + "n" in VERBS)):
            return True
    return any(w.endswith(suf) and w[: -len(suf)] in ADJS for suf in ADJ_ENDINGS)


def is_typo(w, z, entries):
    if z >= 4.0 or w in ALL_LOWER or also_lowercase(w) or wordfreq.zipf_frequency(w, "en", wordlist="large") >= 3.0:
        return False                  # a real form (schrieben, zeichne) or an English word (later)
    n = len(w)
    if n < 3 or w.endswith(("en", "ts")):    # schrieben, flogen, sagts: real forms, not typos
        return False
    # only swapped letters: other one-letter differences are too often real forms (ganze/ganzer)
    cands = {w[:i] + w[i + 1] + w[i] + w[i + 2:] for i in range(n - 1)} - {w}
    return any(c in entries and entries[c][1] >= z + TYPO_GAP for c in cands)


def display_form(w, standalone_lower, capitalized, any_lower):
    if w in standalone_lower:
        return w
    if w in capitalized and also_lowercase(w):
        return w
    if w in capitalized:
        return capitalized[w]
    if w in any_lower:
        return w
    for suf in SUFFIXES:              # inflected nouns: Häusern -> Häuser, Autos -> Auto
        stem = w[: -len(suf)]
        if len(stem) >= 4 and w.endswith(suf) and stem in capitalized and stem not in any_lower:
            return w[0].upper() + w[1:]
    return w


def main(dic_path, out_path):
    standalone_lower, capitalized, any_lower = hunspell_case(dic_path)
    entries = {}
    for w in wordfreq.top_n_list("de", DE_WORDS, wordlist="large"):
        if WORD.match(w):
            w = restore_sz(w)
            if w in entries:
                continue
            entries[w] = (display_form(w, standalone_lower, capitalized, any_lower), wordfreq.zipf_frequency(w, "de", wordlist="large"))
    typos = [w for w, (_, z) in entries.items() if is_typo(w, z, entries)]
    print(f"dropped {len(typos)} likely typos, e.g. {typos[:150]}")
    for w in typos:
        del entries[w]
    for w in wordfreq.top_n_list("en", EN_WORDS, wordlist="large"):
        if WORD.match(w) and w not in entries:
            entries[w] = ("I" if w == "i" else w, max(0.0, wordfreq.zipf_frequency(w, "en", wordlist="large") - EN_PENALTY))
    for k in [k for k in entries if "ß" in k and k.replace("ß", "ss") in entries and k not in ALL_LOWER]:
        del entries[k]                # aussie -> "außie": the guess was wrong, the ss word exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for key in sorted(entries):
            disp, z = entries[key]
            f.write(f"{key}\t{disp}\t{int(round(z * 100))}\n")
    print(f"{out_path}: {len(entries)} words")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
