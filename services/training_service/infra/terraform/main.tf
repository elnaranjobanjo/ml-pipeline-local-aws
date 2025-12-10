provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  endpoints = {
    s3         = "http://localhost:4566"
    ecr        = "http://localhost:4566"
    ecs        = "http://localhost:4566"
    iam        = "http://localhost:4566"
    logs       = "http://localhost:4566"
  }
}

terraform {
  required_version = ">= 1.5.0"
}
