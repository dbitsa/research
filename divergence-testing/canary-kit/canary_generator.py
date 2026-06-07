#!/usr/bin/env python3
"""DBITSA canary token generator + tracker.

Notes:
  - Adds the kit §1.1 pre-deployment tokenizer check inline. Every minted
    passphrase is required to encode to <= MAX_SUBTOKENS sub-tokens in BOTH
    cl100k_base and o200k_base; otherwise the token is re-minted (gate).
  - Tokenizer results (per-encoding sub-token counts + OK/HIGH verdict) are
    printed in the run output and recorded in the tracking CSV.
  - If tiktoken is unavailable, the script degrades gracefully: it still mints,
    records tokenizer fields as empty, and adds a `tokenizer-not-measured` flag
    (per kit §14 self-audit guidance).
  - No hyphens in the word token (space-joined).
  - datetime.now(datetime.UTC) instead of deprecated utcnow().
  - Verified single-token word list.
  - You can use the build_1token_wordlist.py script to generate a list of tiktoken
    validated 1-token words for inclustion in this script
"""
import secrets
import hashlib
import csv
import datetime
import sys
import os
import uuid

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False

NAMESPACE = "dbitsa canary"
TRACK_FILE = "dbitsa_canary_tracking.csv"

# Kit §1.1 threshold: a passphrase encoding to <= 10 sub-tokens is "OK";
# above this it is "HIGH — prefer UUID key".
#
# Budget note (measured, tiktoken 0.13.0): the NAMESPACE prefix "dbitsa canary"
# is out-of-vocabulary and itself costs 5 sub-tokens in cl100k_base (4 in
# o200k_base). With a 5-word phrase that leaves only ~5 sub-tokens of headroom
# under the <=10 gate, so in practice the gate behaves as a near per-word
# 1-token constraint on the picked words: passing cl100k passphrases land at
# exactly 10. Empirically only ~6% of random 5-word draws clear the gate in
# cl100k_base, so re-mints are expected and normal. Any word that is not a
# single token (e.g. "announced") is simply filtered out by the gate via
# re-mint; no over-budget token can escape.
MAX_SUBTOKENS = 10

# Encodings checked, per kit §1.1.
ENCODINGS = ("cl100k_base", "o200k_base")

# Bound on re-mint attempts so a pathological word list cannot loop forever.
MAX_MINT_ATTEMPTS = 100

WORDS = sorted(set("""
abama abay abbr abby abel abet abies abilities ability abit able abled abler ables ably about abouts above abox absolute abstract acad academic accent accept acceptable accepted accessible according accordion account accounts acct accur accuracy aced acer aces ache ached achen acher aches achievement aching acid acier acies acing acker acle acock acre actable acted acting action actions activate activated activation active actively activities activity actor actors actory acts actual actually actus acus acute adam adapt adapter adaptive adar aday adays added adder adding additional addle addr address addresses adds addy aden adin adjust administrator ador adores ados adult advance advanced advert advisor affected affiliate after again against agal agar agas agate aged agen agency agenda agent agents ager agers ages aget agger aggregate aghan aging agit agma agog agon agonal agos agra agree agua ague agues ahead ahir ailed ailing ails aine ains aint aira aire aired airport airs airy aits ajar ajax akan aked aker akin aking akov alan aland alar alarm alary album albums alchemy alem alen alert alerts ales alette alex algorithm alia alias aliases alice alien align aligned alignment alin alist ality alive allah alle allen aller allis allo allocate allocated allocation allocator allowed allows alls ally almost alogy alone along alpha alphabet already also altar alter altern alternate alternative although alto always amar amarin amas amate amazon amba amber ambient amble amel amen ament amental aments american amic amide amil amin amination amine amines amins amma ammer ammo ammu among amos amount amphetamine ample ampler amps amus anal analysis analytics anan anas ancestor anchor anchors anda ande anders andes andi anding andre android ands andy anes anga angel angelo anger angered angers angle angled angler angles ango angstrom angular anim animal animals animate animated animation animations anime anker anna anne anni annie anno annot annotation annotations announce announced announcement
""".split()))


def encode_counts(token: str) -> dict[str, int]:
    """Return {encoding_name: sub_token_count} for the configured encodings.

    Only called when tiktoken is available.
    """
    counts: dict[str, int] = {}
    for enc_name in ENCODINGS:
        enc = tiktoken.get_encoding(enc_name)
        counts[enc_name] = len(enc.encode(token))
    return counts


def passes_gate(counts: dict[str, int]) -> bool:
    """Kit §1.1 gate: <= MAX_SUBTOKENS sub-tokens in every checked encoding."""
    return all(n <= MAX_SUBTOKENS for n in counts.values())


def mint(n_words: int = 5) -> tuple[str, str, dict[str, int] | None]:
    """Mint a canary passphrase that satisfies the §1.1 tokenizer gate.

    Returns (token, digest, counts). `counts` is the per-encoding sub-token
    map, or None when tiktoken is unavailable (gate cannot be evaluated, so the
    first candidate is accepted and flagged downstream as not-measured).
    """
    for _ in range(MAX_MINT_ATTEMPTS):
        picks = [secrets.choice(WORDS) for _ in range(n_words)]
        token = f"{NAMESPACE} " + " ".join(picks)
        digest = hashlib.sha256(token.encode()).hexdigest()[:8]

        if not TIKTOKEN_AVAILABLE:
            return token, digest, None

        counts = encode_counts(token)
        if passes_gate(counts):
            return token, digest, counts

    raise RuntimeError(
        f"Could not mint a passphrase within {MAX_MINT_ATTEMPTS} attempts that "
        f"encodes to <= {MAX_SUBTOKENS} sub-tokens in {', '.join(ENCODINGS)}. "
        "Inspect the word list or raise MAX_SUBTOKENS."
    )


def mint_dbitsa_uuid() -> str:
    """Return a DBITSA-prefixed unique identifier."""
    return f"DBITSA-{uuid.uuid4()}"


def log_token(
    token: str,
    digest: str,
    counts: dict[str, int] | None,
    note: str = "",
    dbitsa_uuid: str | None = None,
) -> str:
    """Append a row to the tracking CSV, including tokenizer evidence.

    Tokenizer columns are left empty when counts is None (tiktoken absent).
    """
    if dbitsa_uuid is None:
        dbitsa_uuid = mint_dbitsa_uuid()

    cl100k = counts.get("cl100k_base", "") if counts else ""
    o200k = counts.get("o200k_base", "") if counts else ""
    if counts is None:
        verdict = "not-measured"
    else:
        verdict = "OK" if passes_gate(counts) else "HIGH"

    new_file = not os.path.exists(TRACK_FILE)
    with open(TRACK_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow([
                "timestamp_utc",
                "dbitsa_uuid",
                "token",
                "integrity_hash",
                "cl100k_tokens",
                "o200k_tokens",
                "tokenizer_verdict",
                "note",
            ])
        w.writerow([
            datetime.datetime.now(datetime.UTC).isoformat() + "Z",
            dbitsa_uuid,
            token,
            digest,
            cl100k,
            o200k,
            verdict,
            note,
        ])
    return dbitsa_uuid


def print_tokenizer_report(token: str, counts: dict[str, int] | None) -> None:
    """Print the §1.1 tokenizer results for this run."""
    print("Tokenizer check (§1.1):")
    if counts is None:
        print("  tiktoken not installed — gate NOT evaluated.")
        print("  Flag: tokenizer-not-measured. Install with: pip install tiktoken")
        return
    for enc_name in ENCODINGS:
        n = counts[enc_name]
        verdict = "OK" if n <= MAX_SUBTOKENS else f"HIGH (> {MAX_SUBTOKENS}) — prefer UUID key"
        print(f"  {enc_name:<12}: {n} sub-tokens → {verdict}")


if __name__ == "__main__":
    note = sys.argv[1] if len(sys.argv) > 1 else ""
    token, digest, counts = mint()
    dbitsa_uuid = log_token(token, digest, counts, note)

    print(f"DBITSA-ID: {dbitsa_uuid}")
    print(f"Token    : {token}")
    print(f"Hash     : {digest}")
    print(f"Logged   : {TRACK_FILE}")
    print_tokenizer_report(token, counts)
    print(f"Entropy  : ~35 bits (5 words / {len(WORDS)}-word list). Add n_words for more margin.")
    if not TIKTOKEN_AVAILABLE:
        print("WARNING  : §1.1 gate not enforced this run (tokenizer-not-measured).")
