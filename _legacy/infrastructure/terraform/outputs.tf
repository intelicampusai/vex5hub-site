output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "website_url" {
  description = "Website URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "api_url" {
  description = "API Function URL"
  value       = aws_lambda_function_url.api.function_url
}

output "website_bucket_name" {
  description = "S3 bucket for website files"
  value       = aws_s3_bucket.website.id
}

output "assets_bucket_name" {
  description = "S3 bucket for media assets"
  value       = aws_s3_bucket.assets.id
}

output "data_bucket_name" {
  description = "S3 bucket for dynamic content data"
  value       = aws_s3_bucket.data.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.main.name
}

output "lambda_function_name" {
  description = "Content updater Lambda function name"
  value       = aws_lambda_function.content_updater.function_name
}

output "route53_nameservers" {
  description = "Route 53 nameservers (update at your domain registrar)"
  value       = var.domain_name != "" ? aws_route53_zone.main[0].name_servers : []
}

output "deploy_command" {
  description = "Command to deploy website files"
  value       = "aws s3 sync ./dist s3://${aws_s3_bucket.website.id} --delete --profile rdp"
}

output "invalidate_command" {
  description = "Command to invalidate CloudFront cache"
  value       = "aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.main.id} --paths '/*' --profile rdp"
}
