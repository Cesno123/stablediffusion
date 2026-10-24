"""Builds app/assets/bigrams.tsv: which words tend to follow which, for context-aware suggestions.

Counts word pairs in German text that is freely available on GitHub (Universal Dependencies
HDT and GSD treebanks, the 10kGNAD news articles, Europarl speeches, GermEval 2018 tweets and
GermEval 2021 Facebook comments) plus tools/chat_de.txt, a hand-written list of everyday
chat messages; the colloquial text counts more). Only words in
dict.tsv are kept. "<s>" stands for the start of a sentence.

Output, sorted by the first word: prev <TAB> word:cost,word:cost,...  with cost = -100*log10 P(word | prev)
"""

import collections
import csv
import glob
import math
import os
import re
import sys

TOKEN = re.compile(r"[a-zäöüß]+(?:'[a-z]+)?|[.!?]")
MIN_COUNT, MAX_NEXT = 2, 48
SOCIAL_WEIGHT = 4
CHAT_WEIGHT = 25          # tools/chat_de.txt: hand-written everyday messages, rare in the other sources

csv.field_size_limit(10 ** 8)


def texts(corpus):
    with open(os.path.join(os.path.dirname(__file__), "chat_de.txt"), encoding="utf-8") as f:
        for line in f:
            yield line, CHAT_WEIGHT
    for path in glob.glob(os.path.join(corpus, "*.conllu")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# text = "):
                    yield line[9:], 1
    for path in glob.glob(os.path.join(corpus, "gnad_*.csv")):
        with open(path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter=";", quotechar="'"):
                if len(row) >= 2:
                    yield row[1], 1
    for path in glob.glob(os.path.join(corpus, "europarl_raw", "german", "*")):
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                yield line, 1
    for path in glob.glob(os.path.join(corpus, "germeval2018.*.txt")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                yield re.sub(r"@\w+|\|LBR\|", " ", line.split("\t")[0]), SOCIAL_WEIGHT
    for path in glob.glob(os.path.join(corpus, "ge21_*.csv")):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                yield re.sub(r"@\w+|@USER|@MODERATOR", " ", row.get("comment_text", "")), SOCIAL_WEIGHT


def main(corpus, dict_path, out_path):
    known = set()
    with open(dict_path, encoding="utf-8") as f:
        for line in f:
            known.add(line.split("\t", 1)[0])
    pairs = collections.Counter()
    firsts = collections.Counter()
    tokens = 0
    for text, weight in texts(corpus):
        prev = "<s>"
        for tok in TOKEN.findall(text.lower().replace("’", "'")):
            if tok in ".!?":
                prev = "<s>"
                continue
            tokens += 1
            if tok in known:
                pairs[(prev, tok)] += weight
                firsts[prev] += weight
                prev = tok
            else:
                prev = "?"                    # an unknown word breaks the chain
    by_prev = collections.defaultdict(list)
    for (prev, w), c in pairs.items():
        if prev != "?" and c >= MIN_COUNT:
            by_prev[prev].append((c, w))
    with open(out_path, "w", encoding="utf-8") as f:
        n = 0
        for prev in sorted(by_prev):
            total = firsts[prev]
            best = sorted(by_prev[prev], reverse=True)[:MAX_NEXT]
            f.write(prev + "\t" + ",".join(f"{w}:{round(-100 * math.log10(c / total))}" for c, w in best) + "\n")
            n += len(best)
    print(f"{out_path}: {tokens} tokens read, {len(by_prev)} words with {n} followers")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
