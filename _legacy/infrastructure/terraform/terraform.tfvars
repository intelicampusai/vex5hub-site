# Terraform configuration for VEX V5 Hub
# Domain: vex5hub.com (registered 2026-02-09)

# AWS region (ca-central-1 for Canada residency)
aws_region = "ca-central-1"

# Project name prefix for all resources
project_name = "nighthawks"

# Custom domain name
# NOTE: Domain is currently being registered with AWS Route 53
# Uncomment the line below AFTER domain registration is complete and verified
domain_name = "vex5hub.com"

# Content refresh interval (hours)
content_refresh_hours = 4

# Resource tags
tags = {
  Project     = "VEX-V5-Hub"
  Environment = "production"
  ManagedBy   = "terraform"
  Team        = "3150N-Nighthawks"
  Domain      = "vex5hub.com"
}

# VEX Season ID (190 might be 2024-2025 High Stakes. Please verify for 2025-2026 Push Back)
season_id = 190
