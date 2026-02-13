# DynamoDB Table - Single table design for all VEX V5 Hub data
resource "aws_dynamodb_table" "main" {
  name         = "${var.project_name}-data"
  billing_mode = "PAY_PER_REQUEST"  # Serverless, scales to zero cost when idle
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  # GSI for querying by type (e.g., all teams, all events)
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-data"
  }
}
