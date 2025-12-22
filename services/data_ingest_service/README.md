# Data ingest service

Produces small batches of synthetic market data and stores them in S3 so the downstream feature/model Lambdas have something realistic to work with inside LocalStack.

## Lambda contract

- Input event (all optional):  
  `bucket`, `key` – S3 location for the CSV.  
  `batch_size` – number of synthetic rows to generate (default `32`).  
  `symbol` – string identifier stamped on each row (default `BTC-USD`).
- Output: JSON containing the target S3 path, number of rows written, and a short preview of the generated payload.

Environment variables mirror the same keys (`INGEST_BUCKET`, `INGEST_KEY`, `INGEST_BATCH_SIZE`, `INGEST_SYMBOL`) so Terraform can configure the Lambda without changing the invocation payload.

## Packaging

```
cd services/data_ingest_service
task build
```

Creates `dist/data-ingest-lambda.zip` ready to be wired into Terraform. No external dependencies are packaged; the function only relies on boto3 which is provided by the Lambda runtime.
