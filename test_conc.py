"""
LexAI — Concurrency Test  (zero external dependencies)
=======================================================
Uses only stdlib: asyncio, urllib, json, time, os

Run:
    python test_concurrency.py

Env vars (all optional):
    BASE_URL        http://127.0.0.1:8001
    SINGLE_TIMEOUT  60      seconds — per request when load is low
    CONC_TIMEOUT    120     seconds — per request under concurrent load
    CONCURRENCY     5       simultaneous requests
    STRESS_N        15      total stress requests
"""

import asyncio, json, os, sys, time, urllib.error, urllib.request
from dataclasses import dataclass
from typing import List, Tuple

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL       = os.getenv("BASE_URL",       "http://127.0.0.1:8001")
SINGLE_TIMEOUT = int(os.getenv("SINGLE_TIMEOUT", "60"))   # single / sequential
CONC_TIMEOUT   = int(os.getenv("CONC_TIMEOUT",  "120"))   # concurrent / stress
CONCURRENCY    = int(os.getenv("CONCURRENCY",    "5"))
STRESS_N       = int(os.getenv("STRESS_N",       "15"))

LEGAL_QUERIES = [
    "What is IPC Section 302?",
    "Explain Article 21 of the Indian Constitution.",
    "What are the rights of an arrested person in India?",
    "What is anticipatory bail under CrPC?",
    "Explain cognizable and non-cognizable offences.",
    "What is the Motor Vehicles Act?",
    "Explain habeas corpus petition.",
    "What is the Industrial Disputes Act?",
    "Define defamation under Indian law.",
    "What is Section 498A IPC?",
]

# ── ANSI ──────────────────────────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"
B="\033[1m";  D="\033[2m";  X="\033[0m"

def ok(m):   print(f"  {G}✔{X}  {m}")
def fail(m): print(f"  {R}✗{X}  {m}")
def info(m): print(f"  {C}·{X}  {D}{m}{X}")
def head(m): print(f"\n{B}{m}{X}")
def sep():   print(f"  {'─'*58}")

passed = failed = 0

def check(cond, good, bad):
    global passed, failed
    if cond: ok(good);   passed += 1
    else:    fail(bad);  failed += 1

# ── Result ────────────────────────────────────────────────────────────────────
@dataclass
class R:
    index: int; query: str
    status: int=0; response: str=""; elapsed: float=0.0; error: str=""
    @property
    def ok(self): return self.status == 200 and not self.error

# ── Sync HTTP (runs in thread pool) ───────────────────────────────────────────
def _get(path: str) -> Tuple[int, dict]:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=SINGLE_TIMEOUT) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return e.code, {}
    except Exception as e:             return 0,      {"error": str(e)}

def _post(path: str, payload: dict, timeout: int) -> Tuple[int, dict]:
    req = urllib.request.Request(
        BASE_URL + path, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:    detail = json.loads(e.read().decode())
        except: detail = {}
        return e.code, detail
    except Exception as e: return 0, {"error": str(e)}

# ── Async wrappers ────────────────────────────────────────────────────────────
loop_ref = None

async def aget(path):
    return await asyncio.get_event_loop().run_in_executor(None, _get, path)

async def achat(idx: int, query: str, timeout: int = SINGLE_TIMEOUT) -> R:
    r  = R(index=idx, query=query)
    t0 = time.perf_counter()
    status, data = await asyncio.get_event_loop().run_in_executor(
        None, _post, "/chat", {"message": query}, timeout)
    r.elapsed = time.perf_counter() - t0
    r.status  = status
    if status == 200:   r.response = data.get("response", "")
    elif status == 504: r.error = f"504 Gateway Timeout (agent exceeded {timeout}s)"
    else:               r.error = data.get("detail", data.get("error", f"HTTP {status}"))
    return r

# ── Summary ───────────────────────────────────────────────────────────────────
def summary(results: List[R], label=""):
    good  = [r for r in results if r.ok]
    bad   = [r for r in results if not r.ok]
    times = [r.elapsed for r in good]
    print(f"\n  {B}{label}{X}")
    sep()
    print(f"  Total  : {len(results)}")
    print(f"  {G}Passed{X} : {len(good)}")
    if bad: print(f"  {R}Failed{X} : {len(bad)}")
    if times:
        print(f"  Avg    : {sum(times)/len(times):.1f}s  "
              f"Min: {min(times):.1f}s  Max: {max(times):.1f}s")
    for r in bad:
        print(f"  {R}✗{X} [{r.index:02d}] {r.query[:38]!r:<42} → {r.error}")
    sep()

# ══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH
# ══════════════════════════════════════════════════════════════════════════════
async def test_health():
    head("1 · Health Check")
    t0 = time.perf_counter()
    status, body = await aget("/health")
    elapsed = time.perf_counter() - t0
    check(status == 200,
          f"/health → 200 OK  ({elapsed:.2f}s)",
          f"/health → {status}  (expected 200)")
    check(body.get("status") == "ok",
          'body["status"] == "ok"',
          f'wrong body: {body}')
    check(elapsed < 2.0,
          f"Responded in {elapsed:.2f}s  (< 2s)",
          f"Too slow: {elapsed:.2f}s")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SINGLE / SEQUENTIAL  (SINGLE_TIMEOUT each)
# ══════════════════════════════════════════════════════════════════════════════
async def test_single():
    head(f"2 · Single / Sequential  (timeout={SINGLE_TIMEOUT}s each)")

    r = await achat(0, "What is IPC Section 302?", SINGLE_TIMEOUT)
    check(r.ok and len(r.response) > 10,
          f"Normal query OK  ({r.elapsed:.1f}s, {len(r.response)} chars)",
          f"Normal query FAILED: {r.error}")

    status, _ = await asyncio.get_event_loop().run_in_executor(
        None, _post, "/chat", {"message": ""}, SINGLE_TIMEOUT)
    check(status in (200, 400, 422),
          f"Empty message → {status}  (not 500)",
          f"Empty message crashed server: HTTP {status}")

    status2, _ = await asyncio.get_event_loop().run_in_executor(
        None, _post, "/chat", {"query": "wrong"}, SINGLE_TIMEOUT)
    check(status2 == 422,
          "Missing 'message' key → 422  (Pydantic)",
          f"Missing key → {status2}  (expected 422)")

    info("Running 3 sequential queries …")
    all_ok = True
    for i, q in enumerate(LEGAL_QUERIES[:3]):
        rv = await achat(i, q, SINGLE_TIMEOUT)
        if not rv.ok: all_ok = False; info(f"  [{i}] FAILED: {rv.error}")
        else:         info(f"  [{i}] OK  {rv.elapsed:.1f}s")
    check(all_ok,
          "3 sequential queries all succeeded",
          "One or more sequential queries failed")

# ══════════════════════════════════════════════════════════════════════════════
# 3. CONCURRENT  (CONC_TIMEOUT — extra headroom for queuing + LLM latency)
# ══════════════════════════════════════════════════════════════════════════════
async def test_concurrent():
    head(f"3 · Concurrent Requests  (n={CONCURRENCY}, timeout={CONC_TIMEOUT}s each)")
    queries  = (LEGAL_QUERIES * 5)[:CONCURRENCY]
    tasks    = [achat(i, q, CONC_TIMEOUT) for i, q in enumerate(queries)]
    t0       = time.perf_counter()
    results  = await asyncio.gather(*tasks)
    wall     = time.perf_counter() - t0
    summary(results, f"{CONCURRENCY} simultaneous requests")

    bad = [r for r in results if not r.ok]
    # Classify failures
    timeouts = [r for r in bad if "timeout" in r.error.lower() or "504" in r.error]
    others   = [r for r in bad if r not in timeouts]

    if timeouts:
        info(f"{len(timeouts)} timeout(s) — LLM is slow or thread pool exhausted; "
             f"raise CONC_TIMEOUT or lower CONCURRENCY")
    if others:
        info(f"{len(others)} non-timeout failure(s)")

    check(len(bad) == 0,
          f"All {CONCURRENCY} concurrent requests succeeded  (wall={wall:.1f}s)",
          f"{len(bad)}/{CONCURRENCY} concurrent requests FAILED")

    times = [r.elapsed for r in results if r.ok]
    if len(times) >= 2:
        speedup = sum(times) / wall if wall > 0 else 1
        check(speedup > 1.3,
              f"Concurrency speedup {speedup:.1f}×  (wall={wall:.1f}s)",
              f"Low speedup {speedup:.1f}× — check thread pool size")

# ══════════════════════════════════════════════════════════════════════════════
# 4. BATCHED BURST  (CONC_TIMEOUT each, 500ms between batches)
# ══════════════════════════════════════════════════════════════════════════════
async def test_batched():
    head(f"4 · Batched Burst  (3 × 3 requests, timeout={CONC_TIMEOUT}s each)")
    batch_size  = 3
    all_results: List[R] = []
    for b in range(3):
        start  = (b * batch_size) % len(LEGAL_QUERIES)
        qs     = [LEGAL_QUERIES[(start + i) % len(LEGAL_QUERIES)] for i in range(batch_size)]
        tasks  = [achat(b * batch_size + i, q, CONC_TIMEOUT) for i, q in enumerate(qs)]
        batch  = await asyncio.gather(*tasks)
        all_results.extend(batch)
        bad    = [r for r in batch if not r.ok]
        check(len(bad) == 0,
              f"Batch {b+1}/3 — all {batch_size} OK",
              f"Batch {b+1}/3 — {len(bad)} failures: " + "; ".join(r.error for r in bad))
        await asyncio.sleep(0.5)
    summary(all_results, "3 batches × 3")

# ══════════════════════════════════════════════════════════════════════════════
# 5. STRESS  (10% failure budget, CONC_TIMEOUT each)
# ══════════════════════════════════════════════════════════════════════════════
async def test_stress():
    head(f"5 · Stress Load  (n={STRESS_N}, timeout={CONC_TIMEOUT}s, budget=10% fail)")
    queries = (LEGAL_QUERIES * 10)[:STRESS_N]
    tasks   = [achat(i, q, CONC_TIMEOUT) for i, q in enumerate(queries)]
    results = await asyncio.gather(*tasks)
    summary(results, f"{STRESS_N} total requests")

    bad     = [r for r in results if not r.ok]
    pct     = len(bad) / len(results) * 100
    check(pct <= 10,
          f"Failure rate {pct:.1f}% ≤ 10%",
          f"Failure rate {pct:.1f}% > 10%  ({len(bad)}/{len(results)})")

    await asyncio.sleep(1)
    s, _ = await aget("/health")
    check(s == 200, "Server healthy after stress", f"Server not healthy: HTTP {s}")
    rv = await achat(999, "What is bail?", SINGLE_TIMEOUT)
    check(rv.ok, "Server still serves chat after stress", f"Post-stress chat failed: {rv.error}")

# ══════════════════════════════════════════════════════════════════════════════
# 6. EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════
async def test_edge_cases():
    head("6 · Edge Cases")

    tasks   = [achat(i, "What is Article 21?", CONC_TIMEOUT) for i in range(3)]
    results = await asyncio.gather(*tasks)
    bad     = [r for r in results if not r.ok]
    check(len(bad) == 0,
          "3 identical concurrent queries all succeeded",
          f"{len(bad)}/3 identical queries failed")

    s, _ = await aget("/undefined_route")
    check(s == 404, f"Unknown route → 404", f"Unknown route → {s}")

    r = await achat(0, "What is IPC 302?", SINGLE_TIMEOUT)
    check(isinstance(r.response, str) and len(r.response) > 0,
          f"Response is non-empty string ({len(r.response)} chars)",
          "Response is empty or wrong type")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    print(f"\n{B}{'═'*60}{X}")
    print(f"{B}  LexAI Concurrency Test Suite{X}")
    print(f"  Target         : {C}{BASE_URL}{X}")
    print(f"  Concurrency    : {CONCURRENCY}   Stress: {STRESS_N}")
    print(f"  Single timeout : {SINGLE_TIMEOUT}s   Concurrent timeout: {CONC_TIMEOUT}s")
    print(f"{B}{'═'*60}{X}")

    # Preflight — abort if server is down
    status, _ = await aget("/health")
    if status != 200:
        print(f"\n{R}{B}  Server unreachable at {BASE_URL}  (HTTP {status}){X}")
        print(f"  Start: uvicorn app.main:app --host 0.0.0.0 --port 8001\n")
        sys.exit(1)

    await test_health()
    await test_single()
    await test_concurrent()
    await test_batched()
    await test_stress()
    await test_edge_cases()

    total = passed + failed
    print(f"\n{B}{'═'*60}{X}")
    print(f"{B}  Score: {passed}/{total}{X}")
    if failed == 0: print(f"  {G}{B}All tests passed ✔{X}")
    else:           print(f"  {R}{B}{failed} test(s) failed ✗{X}")
    print(f"{B}{'═'*60}{X}\n")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())