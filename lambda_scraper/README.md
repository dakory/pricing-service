# Competitor collector Lambda

This image contains the asynchronous collection boundary only. The current
adapter deliberately reports `source_not_configured`; replace
`collect_listing_calendar` with an authorized provider implementation that
returns the callback observation schema.

The exact adapter input and raw stay-quote output are documented in
`COLLECTOR_CONTRACT.md`. Price normalization remains in the backend.

## First deployment

1. Create the ECR repository and supporting resources:

   ```sh
   terraform -chdir=infra apply
   ```

2. Build and push an immutable image tag:

   ```sh
   REPOSITORY="$(terraform -chdir=infra output -raw competitor_lambda_repository_url)"
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "${REPOSITORY%/*}"
   docker build -t "$REPOSITORY:v1" lambda_scraper
   docker push "$REPOSITORY:v1"
   ```

3. Create the Lambda from the pushed digest or immutable tag:

   ```sh
   terraform -chdir=infra apply -var "competitor_lambda_image_uri=$REPOSITORY:v1"
   ```

4. Replace the SSM placeholder value and set the same decrypted value as
   `COMPETITOR_CALLBACK_TOKEN` in the backend environment. Set
   `COMPETITOR_SCRAPE_LAMBDA_NAME` from the Terraform output.

The Lambda has no EventBridge schedule and can only be invoked by the
application EC2 role. Reserved concurrency is one.
