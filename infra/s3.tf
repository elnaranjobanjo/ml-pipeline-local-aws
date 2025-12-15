resource "aws_s3_bucket" "dataset" {
  bucket        = "dataset"
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = "artifacts"
}