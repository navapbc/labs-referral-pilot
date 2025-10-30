#!/usr/bin/env python3
import asyncio, aiohttp, time, statistics, argparse, json, sys

DEFAULT_URL = "https://referral-pilot-dev.navateam.com/generate_referrals/run"
DEFAULT_HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}
DEFAULT_PAYLOAD = {
    "query": "My client is hungry and needs transportation",
    "prompt_version_id": "",
    "user_email": "kevinboyer+test@navapbc.com"
}

async def hit(session, url, headers, payload, sem):
    async with sem:
        t0 = time.perf_counter()
        try:
            async with session.post(url, json=payload, headers=headers) as r:
                await r.read()  # drain
                dt = (time.perf_counter() - t0) * 1000.0
                return True, r.status, dt
        except Exception:
            dt = (time.perf_counter() - t0) * 1000.0
            return False, None, dt

async def run(url, headers, payload, total, concurrency):
    sem = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(total=None)
    conn = aiohttp.TCPConnector(limit=0, ssl=None)  # allow many in-flight
    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
        t_start = time.perf_counter()
        tasks = [asyncio.create_task(hit(session, url, headers, payload, sem)) for _ in range(total)]
        results = await asyncio.gather(*tasks)
        wall = time.perf_counter() - t_start

    oks = [dt for ok, status, dt in results if ok and (status is not None) and (200 <= status < 400)]
    fails = [dt for ok, status, dt in results if not (ok and (status is not None) and (200 <= status < 400))]
    latencies = [dt for _, _, dt in results]

    def pct(p, xs):
        if not xs: return float("nan")
        return statistics.quantiles(xs, n=100, method="inclusive")[p-1]

    def fmt(x):
        return "nan" if x != x else f"{x:.2f} ms"

    print(f"URL: {url}")
    print(f"Requests: {total} | Concurrency: {concurrency}")
    print(f"Success: {len(oks)} | Failures: {len(fails)} | Success rate: {(len(oks)/total*100):.1f}%")
    print(f"Wall time: {wall:.3f}s | Throughput: {(total/wall):.2f} req/s")
    if latencies:
        print("Latency (all responses):")
        print(f"  avg: {fmt(statistics.mean(latencies))}")
        print(f"  p50: {fmt(pct(50, latencies))}")
        print(f"  p90: {fmt(pct(90, latencies))}")
        print(f"  p95: {fmt(pct(95, latencies))}")
        print(f"  p99: {fmt(pct(99, latencies))}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Simple parallel load test")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--requests", type=int, default=100, help="Total number of requests")
    ap.add_argument("--concurrency", type=int, default=100, help="Max in-flight requests")
    ap.add_argument("--header", action="append", default=[], help="Extra header key:val (can repeat)")
    ap.add_argument("--payload", type=str, default=None, help="Raw JSON payload string (overrides default)")
    args = ap.parse_args()

    headers = dict(DEFAULT_HEADERS)
    for hv in args.header:
        if ":" not in hv:
            print(f"Bad header format: {hv} (expected key:val)", file=sys.stderr)
            sys.exit(1)
        k, v = hv.split(":", 1)
        headers[k.strip()] = v.strip()

    payload = DEFAULT_PAYLOAD if args.payload is None else json.loads(args.payload)

    asyncio.run(run(args.url, headers, payload, args.requests, args.concurrency))

