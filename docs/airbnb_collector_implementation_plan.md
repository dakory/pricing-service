# Implementation Plan — Airbnb Collector Lambda

Status: **approved** (reviewed in Lavish, feedback adopted) · Scope: code + tests
Backend changes: **already implemented** (`app/competitor_scrapes.py`, `app/api.py`, `app/schemas.py`)

## Goal

Replace the legacy placeholder in `lambda_scraper/lambda_function.py` with the real
Airbnb frontend-API collector implementing the two operations from
`docs/airbnb_collector_implementation_task.md`:

- `calendar` — one `PdpAvailabilityCalendar` request per run, parsed into minimal days;
- `quotes` — sequential `stayCheckout` requests, one per backend-planned quote.

The Lambda only extracts source facts. Interval building, price-method selection and
nightly price math stay in the backend. Production profile: **4 adults**, 0 children /
infants / pets, `IDR`, `locale=en`.

## Anti-bot measures (mandated)

1. **No proxy pools — AWS IP.** Requests are processed strictly sequentially; a
   brand-new HTTP session is opened and closed for every single request (never reused).
2. **TLS fingerprinting — `curl_cffi`.** All HTTP via `curl_cffi.requests` with
   `impersonate="chrome120"` (desktop Chrome JA3/JA4 + HTTP/2 fingerprint). Browser
   headers (User-Agent, `sec-ch-ua`, …) are managed by curl_cffi so they stay
   consistent with the chrome120 fingerprint — the captured fixtures' Chrome 148 /
   mobile Nexus-5 User-Agents are deliberately NOT copied. `x-airbnb-*` business
   headers come from runtime config.
3. **Human simulation.** `time.sleep(random.uniform(1.8, 3.8))` between consecutive
   quote requests (never before the first, never after the last). The calendar stage
   issues one request, so pacing applies to the quote loop.

## Anti-bot measures (adopted in review)

- **Early-stop on ban pattern:** after 2 consecutive HTTP 403 responses, stop issuing
  requests, classify the remaining quotes as `quote_errors`, send the callback.
- **Retry-After on 429:** a single retry for 429/5xx/transport within the deadline
  budget; 429 honors `Retry-After` (capped), otherwise jittered backoff. Never retry
  403 or structural errors.
- **Kill switch via SSM:** `collector_paused` flag in the frontend-config parameter
  makes the Lambda return a `failed` callback without issuing any Airbnb request.
- **Minimal consistent header set:** exactly the captured `x-airbnb-*` set, no
  proxy-ish headers, single fixed chrome120 impersonation (no JA3 rotation).
- **Anomaly tripwire:** ≥ 3 transport failures in one run → classify the remainder as
  errors and fail the batch early.
- **Not adopted:** daily per-listing request cap (backend scheduler scope,
  `app/jobs.py` follow-up only if ban pressure rises).

## Budget (one Lambda call must fit in 60 s)

| Step | Count | Per unit (worst) | Total |
|---|---|---|---|
| Calendar GET | 1 | 2.0 s | 2.0 s |
| Quote requests (sleep + request) | 8 | 3.8 s + 1.5 s | 42.4 s |
| Retries (≤ 1 per quote) | 0–8 | +1.5 s, no extra sleep | 0–12 s |
| Callback POST | 1 | 2.0 s | 2.0 s |
| **Nominal (avg sleep 2.8 s)** | | 8 × 4.3 s + 4 s | **≈ 38 s** |
| **Worst, every quote retried once** | | 8 × 6.8 s + 4 s | **≈ 58 s** |
| Pathological (request timeouts stall) | | deadline guard fires at 50 s | remaining → `quote_errors` |

Constants: request timeout `8 s`, deadline budget `50 s`, sleep `1.8–3.8 s`,
batch limit default `8` (env `AIRBNB_QUOTE_BATCH_LIMIT`, mirrors backend
`competitor_quote_batch_size`).

## Runtime-configurable frontend config (SSM)

API key, client version, both persisted-query SHAs and endpoint paths must be
refreshable **without a redeploy**. They live in one SSM `SecureString` JSON parameter
(`/pricing/competitor-airbnb-config`, seeded with `{}` = use fixture defaults), read
once per invocation (no cross-invocation cache so rotations and the kill switch take
effect on the next invocation). Env var `AIRBNB_FRONTEND_CONFIG_PARAMETER` + IAM
`ssm:GetParameter` (and `kms:Decrypt` on the existing backups key).

## Contracts

Inputs and callbacks match the task doc exactly (see
`docs/airbnb_collector_implementation_task.md`). Invariants:

- Calendar: continuous days, `bookable=false|null → false`; `bookable=true` requires
  `min_nights >= 1`; unknown/truncated envelope or bookable day without valid
  `minNights` → global failure (empty `calendar_days`).
- Quotes: every input `quote_id` classified exactly once in `quotes` or
  `quote_errors`; checkout must follow check-in; unique IDs; batch ≤ configured limit.
- Success requires `…productPriceBreakdown.status.statusCode == "OK"`; price =
  `priceBreakdown.total.total.amountMicros / 1_000_000` (Decimal, string); adjacent
  `currency` strictly `IDR`; never re-apply `SMART_PROMOTION` over `TOTAL`.
- `parser_version`: `airbnb-calendar-v1` / `airbnb-checkout-v1`.
- Never include API keys, payment tokens, headers or full upstream responses in
  callbacks or logs.

## Files

| Path | Change |
|---|---|
| `lambda_scraper/requirements.txt` | New — pin `curl_cffi==0.15.0` |
| `lambda_scraper/Dockerfile` | `COPY requirements.txt` + `pip install` |
| `lambda_scraper/lambda_function.py` | Full rewrite (two operations, curl_cffi transport, parsers, callbacks, SSM config, anti-bot guards) |
| `requirements-dev.txt` | Add curl_cffi for local pytest |
| `tests/test_lambda_scraper.py` | Rewrite to the documented test list |
| `lambda_scraper/README.md`, `COLLECTOR_CONTRACT.md` | Update to the two-operation contract |
| `infra/main.tf` | SSM parameter + IAM + `AIRBNB_FRONTEND_CONFIG_PARAMETER` env |

## Tests

The 10 documented items plus the adopted hardening (all via fake transport;
pytest never touches Airbnb):

1. Calendar parser passes the minimal fixture; `bookable=true/false/null`.
2. Bookable day without `minNights` → structural failure.
3. Checkout parser extracts `1700400` IDR via `amountMicros`.
4. `SMART_PROMOTION` not re-applied over `TOTAL`.
5. All network tests use fake transport (session factory guarded).
6. Calendar and quote events fully validated.
7. Partial quote batch classifies each quote ID once.
8. Callback sent on success, partial success and global failure.
9. No API key / payment tokens in logs or callbacks.
10. `pytest`, `compileall`, `git diff --check` pass.
11. Early-stop after 2 consecutive 403s (request count stops, remainder classified).
12. 429 honors `Retry-After`; kill switch returns `failed` with zero requests.
13. Transport core impersonates chrome120.

## Deployment runbook (documented, not executed)

See `lambda_scraper/README.md` for the updated flow: local gate → seed SSM config →
`docker build -t "$REPOSITORY:v2" lambda_scraper` → push → `terraform apply -var
"competitor_lambda_image_uri=$REPOSITORY:v2"` → `aws lambda invoke` smoke test.
Confirm AWS account, region and ECR target before deploying.
