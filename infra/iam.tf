resource "aws_iam_role" "lambda_role" {
  name = "general-role"

  assume_role_policy = file("./trust_policy.json")
}