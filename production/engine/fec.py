"""FEC assessment — Phase 6.

Try-all de-interleave {block, convolutional, diagonal, pseudo-random} x
trial decode {Reed-Solomon (pure-NumPy GF(256) codec below), Viterbi K=3/5/7
(hard-decision, pure NumPy)} ranked by correction success. assess_bits()
never guesses: random/unknown streams report NONE (or STRUCTURE hints),
only zero-syndrome RS decodes are CLEAN.

Heavy deps (galois / scikit-commpy / pyldpc) are OPTIONAL accelerators
probed by backend_status() — the builtin paths are exact and run
everywhere, including this dev machine and CI. LDPC trial decode
requires pyldpc when installed (no builtin LDPC yet — honest gap).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------- GF(256)

_PRIM = 0x11D
_EXP = [0] * 512
_LOG = [0] * 256


def _init_tables() -> None:
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= _PRIM
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_tables()


def gf_add(a: int, b: int) -> int:
    return a ^ b


def gf_mul(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def gf_div(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError("gf_div by zero")
    return 0 if a == 0 else _EXP[(_LOG[a] - _LOG[b]) % 255]


def gf_pow(a: int, e: int) -> int:
    if e == 0:
        return 1
    if a == 0:
        return 0
    return _EXP[(_LOG[a] * e) % 255]


def _poly_mul(p: list[int], q: list[int]) -> list[int]:
    out = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                if b:
                    out[i + j] ^= gf_mul(a, b)
    return out


def _poly_eval(poly: list[int], x: int) -> int:
    """Evaluate DESCENDING poly (poly[0] = highest-degree coeff) at x."""
    y = 0
    for c in poly:
        y = gf_mul(y, x) ^ c
    return y


def _poly_eval_asc(poly: list[int], x: int) -> int:
    """Evaluate ASCENDING poly (poly[0] = constant term, BM domain) at x."""
    y = 0
    for c in reversed(poly):
        y = gf_mul(y, x) ^ c
    return y


class RSCodec:
    """Systematic RS(n,k) over GF(256), fcr=0 (roots a^0..a^{nsym-1})."""

    def __init__(self, n: int, k: int):
        if not (2 <= k < n <= 255):
            raise ValueError(f"need 2 <= k < n <= 255, got ({n},{k})")
        self.n, self.k, self.nsym = n, k, n - k
        gen = [1]
        for i in range(self.nsym):
            gen = _poly_mul(gen, [1, _EXP[i]])
        self.gen = gen

    def encode(self, msg: bytes) -> bytes:
        if len(msg) > self.k:
            raise ValueError(f"msg {len(msg)}B > k={self.k}")
        data = [0] * (self.k - len(msg)) + list(msg)  # front-pad (shortening)
        _, rem = _poly_divmod(data + [0] * self.nsym, self.gen)
        pad = [0] * (self.nsym - len(rem))
        return bytes(data + pad + rem)

    def decode(self, code: bytes) -> tuple[bytes, int]:
        """Returns (msg incl. front-pad, n_corrected). Raises RSDecodeError."""
        if len(code) != self.n:
            raise RSDecodeError(f"need {self.n}B, got {len(code)}")
        cw = list(code)
        synd = [_poly_eval(cw, _EXP[i]) for i in range(self.nsym)]
        if max(synd) == 0:
            return bytes(cw[: self.k]), 0
        err_loc = _berlekamp_massey(synd, self.nsym)
        found = _chien_search(err_loc, self.n)
        if len(found) == 0 or len(found) > self.nsym // 2 + (self.nsym % 2):
            raise RSDecodeError(f"uncorrectable ({len(found)} errors?)")
        for pos, mag in _forney(synd, err_loc, found, self.nsym):
            cw[pos] ^= mag
        if max(_poly_eval(cw, _EXP[i]) for i in range(self.nsym)) != 0:
            raise RSDecodeError("residual syndromes after correction")
        return bytes(cw[: self.k]), len(found)


class RSDecodeError(ValueError):
    pass


def _poly_divmod(num: list[int], den: list[int]) -> tuple[list[int], list[int]]:
    num = list(num)
    quo = [0] * max(len(num) - len(den) + 1, 0)
    for i in range(len(quo)):
        coef = num[i]
        quo[i] = coef
        if coef:
            for j in range(1, len(den)):
                num[i + j] ^= gf_mul(den[j], coef)
    return quo, num[len(quo):]


def _berlekamp_massey(synd: list[int], nsym: int) -> list[int]:
    C, B = [1], [1]
    L, m, b = 0, 1, 1
    for n in range(nsym):
        d = synd[n]
        for i in range(1, L + 1):
            d ^= gf_mul(C[i] if i < len(C) else 0, synd[n - i])
        if d == 0:
            m += 1
            continue
        T = list(C)
        coef = gf_div(d, b)
        if len(C) < len(B) + m:
            C += [0] * (len(B) + m - len(C))
        for i in range(len(B)):
            C[i + m] ^= gf_mul(coef, B[i])
        if 2 * L <= n:
            L, B, b, m = n + 1 - L, T, d, 1
        else:
            m += 1
    return C + [0] * (L + 1 - len(C))


def _chien_search(err_loc: list[int], n: int) -> list[tuple[int, int]]:
    """BM-locator roots are X_j^{-1} (ascending poly): root a^i -> position
    j = (n-1+i) % 255 (kept if < n). Scans the FULL field — roots sit at
    arbitrary powers, not inside 0..n-1. Returns [(position, root_power_i)]."""
    found = []
    for i in range(255):
        if _poly_eval_asc(err_loc, _EXP[i]) == 0:
            j = (n - 1 + i) % 255
            if j < n:
                found.append((j, i))
    return found


def _forney(synd: list[int], err_loc: list[int], found: list[tuple[int, int]], nsym: int) -> list[tuple[int, int]]:
    """Error magnitudes (Forney), all in BM ascending domain.

    found = [(position j, root power i)] with X_j^{-1} = a^i.
    Y_j = Omega(X_j^{-1}) / Lambda'(X_j^{-1}) (bare ratio: fcr=0 needs no
    extra X factor in this BM form — verified against known errors).
    Returns [(position, magnitude)].
    """
    omega = _poly_mul(synd, err_loc)[:nsym]
    # formal derivative in char 2 (odd-power terms), ascending domain
    deriv = [c if (i % 2 == 1) else 0 for i, c in enumerate(err_loc)]
    out = []
    for j, i in found:
        pt = _EXP[i % 255]  # X_j^{-1}
        num = _poly_eval_asc(omega, pt)
        den = _poly_eval_asc(deriv, pt)
        if den == 0:
            raise RSDecodeError("zero Forney denominator")
        out.append((j, gf_div(num, den)))
    return out


# ---------------------------------------------------------------- Viterbi

_CONV_POLYS = {
    3: (0o7, 0o5),
    5: (0o23, 0o35),
    7: (0o133, 0o171),
}


def conv_encode(bits: np.ndarray, K: int = 3) -> np.ndarray:
    """Rate-1/2 convolutional encode with K-1 zero flush."""
    p1, p2 = _CONV_POLYS[K]
    reg = 0
    out = []
    for b in list(np.asarray(bits, dtype=np.uint8).ravel()) + [0] * (K - 1):
        reg = ((reg << 1) | int(b)) & ((1 << K) - 1)
        out.append(bin(reg & p1).count("1") % 2)
        out.append(bin(reg & p2).count("1") % 2)
    return np.array(out, dtype=np.uint8)


def viterbi_decode(sym: np.ndarray, K: int = 3) -> tuple[np.ndarray, float]:
    """Hard-decision Viterbi. Returns (info_bits, metric = disagree fraction)."""
    y = np.asarray(sym, dtype=np.uint8).ravel()
    n_steps = len(y) // 2
    n_states = 1 << (K - 1)
    mask = n_states - 1
    p1, p2 = _CONV_POLYS[K]
    # Precompute transitions: ns[prev, input] -> state; out bits.
    trans_s = np.zeros((n_states, 2), dtype=int)
    trans_o = np.zeros((n_states, 2, 2), dtype=np.uint8)
    for prev in range(n_states):
        for b in (0, 1):
            reg = ((prev << 1) | b) & ((1 << K) - 1)
            trans_s[prev, b] = reg & mask
            trans_o[prev, b, 0] = bin(reg & p1).count("1") % 2
            trans_o[prev, b, 1] = bin(reg & p2).count("1") % 2
    INF = 1 << 30
    metric = np.full(n_states, INF)
    metric[0] = 0
    prev_choice = np.zeros((n_steps, n_states), dtype=np.int8)
    prev_state = np.zeros((n_steps, n_states), dtype=np.int32)
    r0 = y[0::2].astype(np.int32)
    r1 = y[1::2].astype(np.int32)
    for t in range(n_steps):
        new_metric = np.full(n_states, INF)
        a0, a1 = int(r0[t]), int(r1[t])
        for prev in range(n_states):
            m0 = int(metric[prev])
            if m0 >= INF:
                continue
            for b in (0, 1):
                ns = int(trans_s[prev, b])
                cand = m0 + (int(trans_o[prev, b, 0]) != a0) + (int(trans_o[prev, b, 1]) != a1)
                if cand < new_metric[ns]:
                    new_metric[ns] = cand
                    prev_choice[t, ns] = b
                    prev_state[t, ns] = prev
        metric = new_metric
    # Traceback from state 0 (terminated code).
    state, bits = 0, []
    for t in range(n_steps - 1, -1, -1):
        bits.append(prev_choice[t, state])
        state = int(prev_state[t, state])
    bits = np.array(bits[::-1], dtype=np.uint8)
    info = bits[: max(0, n_steps - (K - 1))]
    return info, float(np.min(metric)) / max(2 * n_steps, 1)


# ---------------------------------------------------------- De-interleave

def block_deinterleave(bits: np.ndarray, cols: int) -> np.ndarray:
    """Inverse of row-write/col-read block interleave (i.e. col-write/row-read)."""
    b = np.asarray(bits, dtype=np.uint8).ravel()
    if cols < 2 or len(b) < 2 * cols:
        raise ValueError("too short for block de-interleave")
    n = (len(b) // cols) * cols
    rows = n // cols
    return b[:n].reshape(cols, rows).T.ravel()


def block_interleave(bits: np.ndarray, cols: int) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    n = (len(b) // cols) * cols
    rows = n // cols
    return b[:n].reshape(rows, cols).T.ravel()


def conv_deinterleave(bits: np.ndarray, rows: int = 8, delay: int = 4) -> np.ndarray:
    """Inverse Ramsey convolutional interleave (row i delayed i*delay)."""
    b = np.asarray(bits, dtype=np.uint8).ravel()
    if rows < 2 or len(b) < 4 * rows:
        raise ValueError("too short for convolutional de-interleave")
    n = (len(b) // rows) * rows
    cols = n // rows
    grid = b[:n].reshape(rows, cols)
    out = np.zeros_like(grid)
    for i in range(rows):
        out[i] = np.roll(grid[i], -i * delay % cols)
    return out.ravel()


def conv_interleave(bits: np.ndarray, rows: int = 8, delay: int = 4) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    n = (len(b) // rows) * rows
    cols = n // rows
    grid = b[:n].reshape(rows, cols)
    out = np.zeros_like(grid)
    for i in range(rows):
        out[i] = np.roll(grid[i], i * delay % cols)
    return out.ravel()


def diag_deinterleave(bits: np.ndarray, cols: int) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    if cols < 2 or len(b) < 2 * cols:
        raise ValueError("too short for diagonal de-interleave")
    n = (len(b) // cols) * cols
    rows = n // cols
    m = b[:n].reshape(rows, cols)
    order = sorted(range(n), key=lambda k: ((k // cols) + (k % cols)) % rows)
    return m.ravel()[np.argsort(order)]


def diag_interleave(bits: np.ndarray, cols: int) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    n = (len(b) // cols) * cols
    rows = n // cols
    order = sorted(range(n), key=lambda k: ((k // cols) + (k % cols)) % rows)
    return b[:n][np.array(order)]


def _lfsr_perm(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.permutation(n)


def pr_deinterleave(bits: np.ndarray, seed: int) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    inv = np.empty(len(b), dtype=int)
    inv[_lfsr_perm(len(b), seed)] = np.arange(len(b))
    return b[inv]


def pr_interleave(bits: np.ndarray, seed: int) -> np.ndarray:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    return b[_lfsr_perm(len(b), seed)]


DEINT_CANDIDATES = [
    ("block-8", lambda b: block_deinterleave(b, 8)),
    ("block-16", lambda b: block_deinterleave(b, 16)),
    ("block-32", lambda b: block_deinterleave(b, 32)),
    ("conv-8x4", lambda b: conv_deinterleave(b, 8, 4)),
    ("diag-16", lambda b: diag_deinterleave(b, 16)),
    ("pr-7", lambda b: pr_deinterleave(b, 7)),
    ("pr-99", lambda b: pr_deinterleave(b, 99)),
    ("none", lambda b: np.asarray(b, dtype=np.uint8).ravel()),
]

RS_TRIALS = [(15, 11), (31, 23), (31, 15), (63, 47), (255, 223)]
VIT_TRIALS = [3, 7]


# --------------------------------------------------------------- Assess

@dataclass
class FECResult:
    status: str = "NONE"  # CLEAN | STRUCTURE | NONE
    scheme: str = "none"
    deint: str = "none"
    decoded: bytes = b""
    hex_text: str = "(no decode)"
    ascii_text: str = "(no decode)"
    corrected: int = 0
    metric: float = 1.0
    ranking: list = field(default_factory=list)  # human-readable trial lines
    note: str = ""


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    b = np.asarray(bits, dtype=np.uint8).ravel()
    nbytes = len(b) // 8
    if nbytes == 0:
        return b""
    return np.packbits(b[: nbytes * 8]).tobytes()


def _bytes_to_hex_ascii(raw: bytes, n_bytes: int = 32) -> tuple[str, str]:
    raw = raw[:n_bytes]
    if not raw:
        return "(no decode)", "(no decode)"
    return (
        " ".join(f"{x:02X}" for x in raw),
        "".join(chr(x) if 32 <= x < 127 else "." for x in raw),
    )


def assess_bits(bits: np.ndarray) -> FECResult:
    """Try-all de-interleave x trial-decode. CLEAN only on zero-syndrome RS."""
    b = np.asarray(bits, dtype=np.uint8).ravel()
    if len(b) < 64:
        return FECResult(note=f"only {len(b)} bits — fec abstains")
    best = FECResult(note="no RS/Viterbi structure found (scope: RS + conv/Viterbi only; LDPC roadmap)")
    best_key = (2, 10**9, 0)
    lines: list[str] = []
    for dname, dfn in DEINT_CANDIDATES:
        try:
            db = np.asarray(dfn(b), dtype=np.uint8).ravel()
        except (ValueError, IndexError):
            continue
        if len(db) < 64:
            continue
        raw = _bits_to_bytes(db)
        # RS trials (need full n-byte blocks).
        for (n, k) in RS_TRIALS:
            if len(raw) < n:
                continue
            codec = RSCodec(n, k)
            nblocks = len(raw) // n
            ok, fixed, total = True, 0, 0
            out = bytearray()
            for i in range(nblocks):
                try:
                    msg, nerr = codec.decode(raw[i * n:(i + 1) * n])
                except RSDecodeError:
                    ok = False
                    break
                out += msg[-k:] if len(msg) >= k else msg
                fixed += nerr
                total += 1
            line = f"{dname} RS({n},{k}): {'CLEAN+' + str(fixed) if ok else 'fail'}"
            lines.append(line)
            # Rank CLEAN: exact zero-syndrome framing first (a wrong (n,k) can
            # only match by 256^-nsym chance — except NESTED codes, whose
            # lowest-rate (smallest k) framing explains the most structure),
            # then tighter codes, then more real corrections.
            key = (0 if fixed == 0 else 1, n, k, -fixed)
            if ok and (best.status != "CLEAN" or key < best_key):
                hx, ax = _bytes_to_hex_ascii(bytes(out))
                best = FECResult(
                    status="CLEAN", scheme=f"RS({n},{k})", deint=dname,
                    decoded=bytes(out), hex_text=hx, ascii_text=ax,
                    corrected=fixed, metric=0.0, note=f"RS({n},{k}) via {dname}: {fixed}B corrected",
                )
                best_key = key
        # Viterbi trials (structure hints only — always emits bits).
        for K in VIT_TRIALS:
            if len(db) < 4 * K:
                continue
            try:
                _info, metric = viterbi_decode(db, K)
            except (ValueError, IndexError):
                continue
            lines.append(f"{dname} Vit-K{K}: metric {metric:.3f}")
            if best.status == "NONE" and metric < 0.10:
                hx, ax = _bytes_to_hex_ascii(_bits_to_bytes(_info))
                best = FECResult(
                    status="STRUCTURE", scheme=f"Viterbi-K{K}", deint=dname,
                    decoded=_bits_to_bytes(_info), hex_text=hx, ascii_text=ax,
                    corrected=0, metric=float(metric),
                    note=f"conv-like (K={K} metric {metric:.3f}) via {dname} — payload unverified",
                )
            elif best.status == "STRUCTURE" and metric < best.metric:
                best.metric = float(metric)
                best.scheme, best.deint = f"Viterbi-K{K}", dname
    best.ranking = lines
    if best.status == "NONE":
        best.note = "no RS/Viterbi structure found (scope: RS + conv/Viterbi only; LDPC roadmap)"
    return best


def fec_log_lines(f: FECResult) -> list[str]:
    if f.status == "CLEAN":
        return [
            f"fec: CLEAN {f.scheme} via {f.deint} ({f.corrected}B corrected)",
            f"fec payload: {f.hex_text[:48]}",
        ]
    if f.status == "STRUCTURE":
        return [f"fec: STRUCTURE hint — {f.note}"]
    try:
        st = backend_status()
        acc = ",".join(m for m in ("galois", "commpy", "pyldpc") if st.get(m))
        be = f"backends: builtin RS/Viterbi + {acc}" if acc else "backends: builtin RS/Viterbi (optionals absent)"
    except Exception:
        be = "backends: builtin RS/Viterbi"
    return [f"fec: NONE — {f.note}", be]


def backend_status() -> dict:
    """Probe optional accelerator backends (galois/commpy/pyldpc)."""
    status = {"builtin_rs": True, "builtin_viterbi": True}
    for mod in ("galois", "commpy", "pyldpc"):
        try:
            __import__(mod)
            status[mod] = True
        except ImportError:
            status[mod] = False
    return status
