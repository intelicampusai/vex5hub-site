terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary provider for ca-central-1
provider "aws" {
  region  = var.aws_region
  profile = "rdp"

  default_tags {
    tags = var.tags
  }
}

# US-East-1 provider for ACM certificates (required for CloudFront)
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = "rdp"

  default_tags {
    tags = var.tags
  }
}
