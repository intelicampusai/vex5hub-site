# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-content-updater-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda policy for S3, CloudFront, DynamoDB, Secrets Manager, and CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Resource = aws_cloudfront_distribution.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/*"
      }
    ]
  })
}

# Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/content-updater"
  output_path = "${path.module}/.build/content-updater.zip"
}

resource "aws_lambda_function" "content_updater" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-content-updater"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "index.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 300  # 5 minutes
  memory_size      = 512

  environment {
    variables = {
      TABLE_NAME             = aws_dynamodb_table.main.name
      DATA_BUCKET_NAME       = aws_s3_bucket.data.id
      CLOUDFRONT_DIST_ID     = aws_cloudfront_distribution.main.id
      PROJECT_NAME           = var.project_name
      SEASON_ID              = var.season_id
    }
  }

  tags = {
    Name = "${var.project_name}-content-updater"
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-api-v3"
  retention_in_days = 14
}

# -----------------------------------------------------------------------------
# API Handler Lambda
# -----------------------------------------------------------------------------

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/api-handler"
  output_path = "${path.module}/.build/api-handler.zip"
}

resource "aws_lambda_function" "api_handler" {
  filename         = data.archive_file.api_zip.output_path
  function_name    = "${var.project_name}-api-v3"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "index.handler"
  source_code_hash = data.archive_file.api_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      TABLE_NAME   = aws_dynamodb_table.main.name
      PROJECT_NAME = var.project_name
      SEASON_ID    = var.season_id
    }
  }

  tags = {
    Name = "${var.project_name}-api-handler"
  }
}

# resource "aws_cloudwatch_log_group" "api_logs" {
#   name              = "/aws/lambda/${var.project_name}-api-handler"
#   retention_in_days = 14
# }

# Function URL (Public API)
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api_handler.function_name
  authorization_type = "AWS_IAM"
  
  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["keep-alive", "date"]
    max_age           = 86400
  }
}

# Allow public access to Function URL
resource "aws_lambda_permission" "api_url_public" {
  statement_id  = "AllowCloudFrontInvoke"
  action        = "lambda:InvokeFunctionUrl"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "cloudfront.amazonaws.com"
  # source_arn    = aws_cloudfront_distribution.main.arn
}

output "api_endpoint" {
  value = aws_lambda_function_url.api.function_url
}
