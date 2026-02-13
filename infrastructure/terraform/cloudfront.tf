# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for ${var.project_name} S3 buckets"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_origin_access_control" "api" {
  name                              = "${var.project_name}-api-oac"
  description                       = "OAC for ${var.project_name} Lambda API"
  origin_access_control_origin_type = "lambda"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Cache Policy
resource "aws_cloudfront_cache_policy" "optimized" {
  name        = "${var.project_name}-cache-policy"
  comment     = "Cache policy aligned with 4-hour content refresh"
  default_ttl = 14400  # 4 hours
  max_ttl     = 86400  # 24 hours
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# CloudFront Distribution
# CloudFront Distribution for Website

# Data sources for CloudFront policies
data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

resource "aws_cloudfront_function" "rewrite_url" {
  name    = "${var.project_name}-rewrite-url"
  runtime = "cloudfront-js-1.0"
  comment = "Rewrite URLs for Next.js static export"
  publish = true
  code    = file("${path.module}/functions/rewrite_url.js")
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "3150N Nighthawks Website"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # North America and Europe

  # Primary origin - Website bucket
  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_id                = "S3-Website"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  # Secondary origin - Assets bucket
  origin {
    domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id                = "S3-Assets"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  # Tertiary origin - Data bucket
  origin {
    domain_name              = aws_s3_bucket.data.bucket_regional_domain_name
    origin_id                = "S3-Data"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  # API Origin (Lambda Function URL)
  origin {
    domain_name = replace(aws_apigatewayv2_api.main.api_endpoint, "https://", "")
    origin_id   = "API"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior - Website (serves HTML, CSS, JS)
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-Website"
    cache_policy_id        = aws_cloudfront_cache_policy.optimized.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.rewrite_url.arn
    }
  }

  # Cache behavior for assets
  ordered_cache_behavior {
    path_pattern           = "/assets/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-Assets"
    cache_policy_id        = aws_cloudfront_cache_policy.optimized.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }


  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "API"
    
    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
    viewer_protocol_policy   = "https-only"
    compress                 = true
  }


  # Specific behavior for config.json (No Caching)
  ordered_cache_behavior {
    path_pattern     = "/data/config.json"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-Data"
    
    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
  }

  # Cache behavior for data files
  ordered_cache_behavior {
    path_pattern           = "/data/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-Data"
    cache_policy_id        = aws_cloudfront_cache_policy.optimized.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  custom_error_response {
    error_code         = 403
    response_code      = 404
    response_page_path = "/404.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Use CloudFront default certificate if no custom domain
  viewer_certificate {
    cloudfront_default_certificate = var.domain_name == "" ? true : false
    acm_certificate_arn            = var.domain_name != "" ? aws_acm_certificate.main[0].arn : null
    ssl_support_method             = var.domain_name != "" ? "sni-only" : null
    minimum_protocol_version       = var.domain_name != "" ? "TLSv1.2_2021" : null
  }

  aliases = var.domain_name != "" ? [var.domain_name, "www.${var.domain_name}"] : []

  tags = {
    Name = "${var.project_name}-cdn"
  }
}

# ACM Certificate (only if domain is specified)
resource "aws_acm_certificate" "main" {
  count = var.domain_name != "" ? 1 : 0

  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "www.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-cert"
  }
}
