resource "aws_iam_role" "general-role" {
  name = "general-role"

  assume_role_policy = file("./trust_policy.json")
}