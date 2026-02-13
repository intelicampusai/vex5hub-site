# Route 53 Hosted Zone (only if domain is specified)
resource "aws_route53_zone" "main" {
  count = var.domain_name != "" ? 1 : 0

  name    = var.domain_name
  comment = "Hosted zone for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-zone"
  }
}

# DNS records for CloudFront
resource "aws_route53_record" "root" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "www" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# ACM Certificate DNS Validation Records
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  count = var.domain_name != "" ? 1 : 0

  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
