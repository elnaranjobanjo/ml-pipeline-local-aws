resource "data_ingestion" "data_ingestion" {
  function_name = "ingestion"

  role    = aws_iam_role.general-role.arn
  runtime = "python3.11"
  handler = "handler.lambda_handler"

  filename = "${path.module}/../services/data_ingest_service/dist/data-ingest-lambda.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../services/data_ingest_service/dist/data-ingest-lambda.zip"
  )

  environment {
    variables = {
      DATASET_BUCKET  = aws_s3_bucket.ml-data-demo.bucket
    }
  }
}
