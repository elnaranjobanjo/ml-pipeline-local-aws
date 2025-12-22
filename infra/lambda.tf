resource "aws_lambda_layer_version" "training_deps" {
  layer_name = "training-deps"

  filename = "${path.module}/../services/training_service/dist/ml-deps-layer.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../services/training_service/dist/ml-deps-layer.zip"
  )

  compatible_runtimes = ["python3.11"]
}


resource "aws_lambda_function" "training" {
  function_name = "training"

  role    = aws_iam_role.general-role.arn
  runtime = "python3.11"
  handler = "handler.lambda_handler"

  filename = "${path.module}/../services/training_service/dist/training-lambda.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../services/training_service/dist/training-lambda.zip"
  )

  layers = [
    aws_lambda_layer_version.training_deps.arn
  ]

  environment {
    variables = {
      DATASET_BUCKET  = aws_s3_bucket.dataset.bucket
      ARTIFACT_BUCKET = aws_s3_bucket.artifacts.bucket
    }
  }
}
