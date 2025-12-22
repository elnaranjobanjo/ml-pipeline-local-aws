resource "aws_lambda_layer_version" "model_deps" {
  layer_name = "model-deps"

  filename = "${path.module}/../services/model_service/dist/ml-deps-layer.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../services/model_service/dist/ml-deps-layer.zip"
  )

  compatible_runtimes = ["python3.11"]
}


resource "aws_lambda_function" "model" {
  function_name = "model"

  role    = aws_iam_role.general-role.arn
  runtime = "python3.11"
  handler = "handler.lambda_handler"

  filename = "${path.module}/../services/model_service/dist/model-lambda.zip"
  source_code_hash = filebase64sha256(
    "${path.module}/../services/model_service/dist/model-lambda.zip"
  )

  layers = [
    aws_lambda_layer_version.model_deps.arn
  ]

  environment {
    variables = {
      DATASET_BUCKET  = aws_s3_bucket.dataset.bucket
      ARTIFACT_BUCKET = aws_s3_bucket.artifacts.bucket
    }
  }
}
