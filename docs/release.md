# Release procedure

Backend and dashboard are released together. Each release uses the current git
commit as an immutable image tag; `latest` is not used for production.

## Build and publish

From the repository root:

```bash
make release RELEASE_SHA="$(git rev-parse --short=12 HEAD)"
```

This publishes both images to the existing ECR repository:

```text
pricing-service:api-<sha>
pricing-service:dashboard-<sha>
```

Do not reuse a tag: ECR rejects overwriting immutable release tags.
The repository lifecycle keeps the six newest release images in total.

## Deploy on EC2

Set the image references in `/opt/pricing-service/deployment.env` and recreate
both application containers:

```bash
IMAGE_TAG=<sha>
API_IMAGE=870388460670.dkr.ecr.us-east-1.amazonaws.com/pricing-service:api-<sha>
DASHBOARD_IMAGE=870388460670.dkr.ecr.us-east-1.amazonaws.com/pricing-service:dashboard-<sha>
docker compose --env-file /opt/pricing-service/deployment.env pull api dashboard worker
docker compose --env-file /opt/pricing-service/deployment.env up -d --force-recreate api dashboard worker
```

Run the smoke test from an operator machine:

```bash
scripts/release_smoke.sh https://pricing.nicer.homes <sha>
```

The API `/version` response identifies the backend image. The dashboard
`/dashboard-version` route confirms that the frontend container is serving the release.
The deployment is incomplete if either container is not recreated.
