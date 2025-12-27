# ml-pipeline-local-aws

Infrastructure-as-code sandbox that spins up an end-to-end ML pipeline on AWS using Terraform and LocalStack. Each stage of the pipeline is represented by a focused AWS Lambda so new ideas can be prototyped quickly and safely, while pytest-backed unit tests keep the CI/CD feedback loop tight.

## What's inside

- **Infrastructure defined in Terraform** (`infra/`) to provision IAM roles, S3 buckets, and Lambda functions against LocalStack endpoints. Point it to a real AWS account when you are ready to graduate from local testing.
- **Five services** (`services/*_service`) standing in for the classic pipeline stages: data ingest, feature engineering, model training, inference, and monitoring. Every service packages to a Lambda-compatible ZIP in its own `dist/` folder.
- **Tests ready for CI/CD** via `pytest`. Running `task test` exercises all Lambda entry points so your Terraform apply will never ship untested code.
- **Taskfile automation** for repeatable local workflows like starting LocalStack, syncing Python dependencies with `uv`, running tests, and building artifacts.

## Prerequisites

- Python 3.10+ and [uv](https://github.com/astral-sh/uv) for dependency management
- Docker + Docker Compose to run LocalStack
- Terraform CLI (v1.5+) for applying infrastructure changes
- Taskfile (or just run the equivalent commands manually)

## Quick start

1. **Install deps**
   ```bash
   task deps
   ```
   or `uv sync` if you prefer to run commands manually.
2. **Bring up LocalStack**
   ```bash
   task up
   ```
3. **Run the test suite**
   ```bash
   task test
   ```
   Each service ships with tests under `services/<name>/tests`, so failures pinpoint exactly which Lambda needs attention before merging.
4. **Package a Lambda**
   ```bash
   cd services/data_ingest_service
   task build
   ```
   Repeat per service as you iterate.
5. **Apply Terraform**
   ```bash
   cd infra
   terraform init
   terraform apply
   ```
   Terraform will upload the built ZIPs, wire environment variables, and create IAM/S3 resources that mirror the pipeline topology.

## Project layout

```
.
├── infra/                     # Terraform IaC targeting LocalStack (or AWS with config tweaks)
├── services/
│   ├── data_ingest_service/   # Generates sample market data
│   ├── feature_service/       # Transforms ingested data into features
│   ├── model_service/         # Placeholder training Lambda
│   ├── inference_service/     # Lightweight scoring Lambda
│   └── monitoring_service/    # Stub for drift/metrics checks
├── localstack-docker-compose.yml
├── Taskfile.yml               # Convenience commands (deps, up, test)
└── pyproject.toml             # Shared dependencies for Lambdas + tests
```

## Workflow tips

- Use LocalStack for tight iteration loops, then point the Terraform provider at AWS by swapping the endpoint configuration when you need to validate against the cloud.
- Keep Lambda-specific dependencies inside each service directory; common test utilities can live at the repo root.
- Extend the pytest suite whenever you touch business logic so CI/CD stays trustworthy—the lightweight Lambdas make tests fast enough to run on every push.
