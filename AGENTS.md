# Repository Guidelines

## Project Structure & Module Organization

- `app/main.py` defines the FastAPI application and its HTTP routes.
- `requirements.txt` contains the Python runtime dependencies.
- `Dockerfile` packages the service and starts Uvicorn on port `8000`.
- `Makefile` provides Docker build and AWS ECR deployment shortcuts.
- `infra/` contains Terraform configuration for ECR, EC2, IAM, networking, and instance bootstrap.

Keep application modules under `app/`. Add tests under `tests/`, mirroring application paths where practical (for example, `tests/test_main.py`).

## Build, Test, and Development Commands

- `python -m venv .venv && source .venv/bin/activate` creates and activates a local environment.
- `pip install -r requirements.txt` installs FastAPI and Uvicorn.
- `uvicorn app.main:app --reload` runs the service locally with auto-reload.
- `docker build -t pricing-service .` builds a local container image.
- `make build` builds the `linux/amd64` deployment image.
- `make push` authenticates to the configured AWS ECR registry, tags, and pushes the image.
- `terraform -chdir=infra fmt -check` verifies Terraform formatting.
- `terraform -chdir=infra validate` validates the infrastructure configuration.

`make deploy` publishes an image; confirm the AWS account, region, and ECR target before running it.

## Coding Style & Naming Conventions

Use four-space indentation and PEP 8 conventions for Python. Name functions and modules with `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`. Keep route handlers small and move reusable business logic into focused modules under `app/`.

Format Terraform with `terraform fmt`. Use descriptive `snake_case` resource and variable names consistent with the existing files.

## Testing Guidelines

No automated test suite is currently configured. New behavior should include `pytest` tests using FastAPI's `TestClient`. Name files `test_*.py` and test functions `test_<behavior>`. Run the suite with `pytest`; add testing dependencies to a dedicated development requirements file if introduced.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no established commit convention can be inferred. Use concise, imperative subjects such as `Add price lookup endpoint`. Keep commits focused.

Pull requests should explain the change, list verification commands, link relevant issues, and call out API or Terraform effects. Include request/response examples for endpoint changes and a `terraform plan` summary for infrastructure changes.

## Security & Configuration

Never commit AWS credentials, secrets, local `.env` files, or Terraform state. Review account IDs, regions, network exposure, and IAM changes before deployment.
