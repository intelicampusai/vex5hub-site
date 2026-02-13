# EventBridge Scheduler for content updates every 4 hours
resource "aws_scheduler_schedule" "content_update" {
  name       = "${var.project_name}-content-update"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(${var.content_refresh_hours} hours)"

  target {
    arn      = aws_lambda_function.content_updater.arn
    role_arn = aws_iam_role.scheduler_role.arn

    retry_policy {
      maximum_retry_attempts = 3
    }
  }
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name = "${var.project_name}-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.content_updater.arn
      }
    ]
  })
}

# Permission for EventBridge to invoke Lambda (backup for direct invocation)
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.content_updater.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.content_update.arn
}
