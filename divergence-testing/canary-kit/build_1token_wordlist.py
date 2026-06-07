#!/usr/bin/env python3
import csv
import random
import re
import sys
import urllib.request
from pathlib import Path

import tiktoken

WORDLIST_SOURCES = [
    "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
]

OUT_CSV = "safe_pool_dual_token_words.csv"
OUT_TXT = "safe_pool_dual_token_words.txt"
MIN_WORDS = 250
SEED = 20260606

REFUSAL_BLACKLIST = {
    "refuse","refusal","deny","denial","blocked","ban","banned","forbidden","unsafe",
    "harm","harmful","illegal","crime","criminal","weapon","explosive","malware",
    "phishing","fraud","abuse","attack","jailbreak","bypass","override","ignore"
}

SHORTFORM_BLACKLIST = {
    "usa","uk","eu","un","nato","fbi","cia","nsa","cpu","gpu","api","sdk","cli",
    "html","http","https","json","yaml","xml","sql","ssh","tls","ssl","dns","ip",
    "aws","gcp","ibm","msft","aapl","tsla"
}

ADDITIONAL_BLACKLIST = {
    "alpha","beta","gamma","delta","omega","lambda","sigma","tau","zeta","eta","theta",
    "iota","kappa","mu","nu","xi","omicron","pi","rho","chi","psi","upsilon","phi"
}

COMMON_ABBREV_RE = re.compile(r"^(?:[a-z]{1,3}|[bcdfghjklmnpqrstvwxyz]{2,5})$")
ALPHA_RE = re.compile(r"^[a-z]+$")
VOWEL_RE = re.compile(r"[aeiouy]")


def load_words():
    merged = set()
    for url in WORDLIST_SOURCES:
        data = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", errors="ignore")
        for line in data.splitlines():
            w = line.strip().lower()
            if ALPHA_RE.fullmatch(w):
                merged.add(w)
    return merged


def looks_like_shortform(w: str) -> bool:
    if len(w) <= 2:
        return True
    if w in SHORTFORM_BLACKLIST or w in ADDITIONAL_BLACKLIST:
        return True
    if len(w) <= 4 and not VOWEL_RE.search(w):
        return True
    if len(w) <= 3 and COMMON_ABBREV_RE.fullmatch(w):
        return True
    return False


def allowed_word(w: str) -> bool:
    if not ALPHA_RE.fullmatch(w):
        return False
    if looks_like_shortform(w):
        return False
    if w in REFUSAL_BLACKLIST:
        return False
    return True


def dual_single_token_words(words):
    enc1 = tiktoken.get_encoding("cl100k_base")
    enc2 = tiktoken.get_encoding("o200k_base")
    kept = []
    for w in sorted(words):
        if not allowed_word(w):
            continue
        if len(enc1.encode(w)) == 1 and len(enc2.encode(w)) == 1:
            kept.append(w)
    return kept


def diversify_sample(words, n=250, seed=SEED):
    rng = random.Random(seed)
    by_len = {}
    for w in words:
        by_len.setdefault(len(w), []).append(w)
    for vals in by_len.values():
        rng.shuffle(vals)

    lengths = sorted(by_len)
    result = []
    seen = set()

    while len(result) < min(n, len(words)):
        progressed = False
        for L in lengths:
            bucket = by_len[L]
            while bucket:
                w = bucket.pop()
                if w not in seen:
                    result.append(w)
                    seen.add(w)
                    progressed = True
                    break
            if len(result) >= min(n, len(words)):
                break
        if not progressed:
            break
    return result


def main():
    words = load_words()
    kept = dual_single_token_words(words)
    sample = diversify_sample(kept, MIN_WORDS)
    if len(sample) < MIN_WORDS:
        print(f"ERROR: only {len(sample)} qualifying words found", file=sys.stderr)
        sys.exit(1)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word"])
        for w in sample:
            writer.writerow([w])

    Path(OUT_TXT).write_text(" ".join(sample) + "\n", encoding="utf-8")

    print(f"qualifying_total={len(kept)}")
    print(f"selected={len(sample)}")
    print(f"csv={OUT_CSV}")
    print(f"txt={OUT_TXT}")

if __name__ == "__main__":
    main()
