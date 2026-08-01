# Competitor collector Lambda

This image implements the Airbnb frontend-API collector with the two documented
operations (`calendar`, `quotes`). The Lambda extracts source facts only; the
backend owns interval building, price-method selection and nightly price math.
The exact event and callback shapes are documented in `COLLECTOR_CONTRACT.md` and
`docs/airbnb_collector_implementation_task.md`.

Anti-bot posture: no proxy pools — requests are strictly sequential, each with a
brand-new `curl_cffi` session impersonating desktop Chrome 120
(`impersonate="chrome120"`), with a randomized `sleep(uniform(1.8, 3.8))` between
consecutive quote requests.

## Runtime configuration

- `BACKEND_CALLBACK_URL` — callback endpoint (unified
  `/api/internal/competitor-observations` dispatcher by default).
- `BACKEND_CALLBACK_TOKEN_PARAMETER` — SSM parameter holding the bearer token.
- `AIRBNB_FRONTEND_CONFIG_PARAMETER` — SSM `SecureString` JSON with
  `api_key`, `client_version`, `calendar_sha`, `checkout_sha`, optional
  `calendar_path` / `checkout_path`, and `collector_paused` (kill switch).
  An empty object `{}` uses the fixture defaults baked into the image.
- Optional tuning env vars (defaults in parentheses): `AIRBNB_QUOTE_BATCH_LIMIT`
  (8), `AIRBNB_REQUEST_TIMEOUT` (8), `AIRBNB_DEADLINE_BUDGET` (50),
  `AIRBNB_SLEEP_MIN` (1.8), `AIRBNB_SLEEP_MAX` (3.8).

## Local development

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/test_lambda_scraper.py
python -m compileall app lambda_scraper
git diff --check
```

All network tests use a fake transport; pytest never contacts Airbnb.

## Deployment

1. Create the ECR repository and supporting resources:

   ```sh
   terraform -chdir=infra apply
   ```

2. Build and push an immutable image tag:

   ```sh
   REPOSITORY="$(terraform -chdir=infra output -raw competitor_lambda_repository_url)"
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "${REPOSITORY%/*}"
   docker build -t "$REPOSITORY:v2" lambda_scraper
   docker push "$REPOSITORY:v2"
   ```

3. Seed the runtime config (fixture defaults are used while the parameter is
   `{}`; update it later without a redeploy when Airbnb rotates keys/SHAs):

   ```sh
   aws ssm put-parameter \
     --name "/pricing/competitor-airbnb-config" \
     --type SecureString --overwrite \
     --value '{"api_key":"<from fixture>","client_version":"<from fixture>","calendar_sha":"<from fixture>","checkout_sha":"<from fixture>"}'
   ```

4. Create the Lambda from the pushed tag:

   ```sh
   terraform -chdir=infra apply -var "competitor_lambda_image_uri=$REPOSITORY:v2"
   ```

5. Set the SSM placeholder value of `competitor-callback-token` and mirror it as
   `COMPETITOR_CALLBACK_TOKEN` in the backend environment. Set
   `COMPETITOR_SCRAPE_LAMBDA_NAME` from the Terraform output.

6. Smoke-test both operations:

   ```sh
   aws lambda invoke --function-name pricing-service-competitor-collector \
     --payload '{"operation":"calendar","run_id":1,"competitor_listing_id":1,
       "external_listing_id":"...","listing_url":"https://www.airbnb.com/rooms/...",
       "start_date":"2026-08-01","month_count":12}' out.json
   aws lambda invoke --function-name pricing-service-competitor-collector \
     --payload '{"operation":"quotes","run_id":1,"batch_id":1,
       "competitor_listing_id":1,"external_listing_id":"...",
       "quotes":[{"quote_id":"q_1","check_in_date":"2026-08-03","check_out_date":"2026-08-04"}]}' out.json
   ```

Confirm the AWS account, region and ECR target before deploying. The Lambda has
no EventBridge schedule and can only be invoked by the application EC2 role.
Reserved concurrency is one.
