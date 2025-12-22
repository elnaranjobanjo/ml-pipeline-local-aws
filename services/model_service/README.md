# Model service

Implements the “model” stage of the ML workflow (training plus artifact management) as a standalone AWS Lambda function so it can be demonstrated entirely inside LocalStack.

## Layout

- `src/train.py` – core training routine (CSV from S3, summarize with stdlib + boto3 only, emit metrics, upload JSON artifact).
- `src/handler.py` – AWS Lambda entrypoint that wraps `run_training`.
- `Taskfile.yml` – helper targets to package, deploy, and invoke the Lambda.
- `infra/terraform` – Terraform that registers the Lambda and wires environment variables.

## Expected data

The trainer downloads a labeled CSV from S3. By default it looks for:

- Bucket: `ml-data-demo`
- Key: `data/btc_candles_labeled_sample.csv`

After summarizing, a compact JSON artifact with dataset metadata is uploaded to S3 as well. Configure the outputs via:

- `TRAINING_ARTIFACT_BUCKET` (default `artifacts`)
- `TRAINING_ARTIFACT_KEY` (default `models/training_pipeline.pkl`)

Upload whatever dataset you need into LocalStack before invoking the Lambda. Example command:

```bash
./scripts/aws-local.sh s3 cp ./path/to/dataset.csv s3://ml-data-demo/data/btc_candles_labeled_sample.csv
```

Adjust the bucket/key via Terraform variables (`training_data_bucket`, `training_data_key`) or by setting the corresponding environment variables before packaging.

## Lambda workflow

All commands below are run from `services/model_service`.

1. **Package dependencies + source**  
   ```
   task lambda:package
   ```  
   Produces `dist/model-lambda.zip` that Terraform consumes. This step needs internet connectivity to download Python packages the first time it runs.

2. **Deploy to LocalStack**  
   ```
   task lambda:deploy
   ```  
   Runs `terraform init && terraform apply -auto-approve`, registering the Lambda with the endpoint defined in `.env` (`http://localhost:4566`).

3. **Invoke**  
   ```
   task lambda:invoke
   ```  
   Calls `aws lambda invoke ...` through the repo-scoped AWS wrapper and writes the response body to `tmp/lambda-response.json`. Sample output:
   ```jsonc
   {
     "StatusCode": 200,
     "ExecutedVersion": "$LATEST",
     "FunctionError": null,
     "Payload": "{\"metrics\": {\"accuracy\": 0.71, \"f1\": 0.68}}"
   }
   ```

Customize the invocation payload (bucket, key, test split, etc.) by editing the `lambda:invoke` task or by running the wrapper script directly:

```bash
../../scripts/aws-local.sh lambda invoke \
  --function-name model-service \
  --payload '{"bucket": "ml-data-demo", "test_size": 0.3}' \
  tmp/lambda-response.json
```

## Tearing down

Use Terraform to destroy the Lambda resources when you’re done:

```bash
cd infra/terraform
terraform destroy -auto-approve
```
