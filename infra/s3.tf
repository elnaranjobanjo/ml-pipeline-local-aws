resource "aws_s3_bucket" "dataset" {
  bucket        = "ml-data-demo"
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = "artifacts"
}