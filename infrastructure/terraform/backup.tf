# AWS Backup setup for DynamoDB daily snapshots retained 90 days

resource "aws_iam_service_linked_role" "backup" {
  aws_service_name = "backup.amazonaws.com"
}

resource "aws_backup_vault" "main" {
  name        = "${var.project_name}-backup-vault"
  kms_key_arn = null

  tags = {
    Name = "${var.project_name}-backup-vault"
  }
}

resource "aws_backup_plan" "daily" {
  name = "${var.project_name}-daily-backup"

  rule {
    rule_name         = "daily-dynamodb-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 7 * * ? *)" # 07:00 UTC daily

    lifecycle {
      delete_after = 90
    }
  }
}

resource "aws_backup_selection" "dynamodb" {
  name         = "${var.project_name}-dynamodb-selection"
  plan_id      = aws_backup_plan.daily.id
  iam_role_arn = aws_iam_service_linked_role.backup.arn

  resources = [
    aws_dynamodb_table.main.arn,
  ]
}
