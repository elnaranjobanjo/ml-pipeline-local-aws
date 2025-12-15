resource "aws_lambda_function" "training" {
  function_name = "training"

  role   = aws_iam_role.lambda_role.arn
  runtime = "python3.11"
  handler = "lambda_function.lambda_handler"

  filename         = "${path.module}/../training_service/training-lambda.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../training_service/training-lambda.zip"
  )

  environment {
    variables = {
      DATASET_BUCKET  = aws_s3_bucket.dataset.bucket
      ARTIFACT_BUCKET = aws_s3_bucket.artifacts.bucket
    }
  }
}