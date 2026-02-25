variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ca-central-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "vex5hub"
}

variable "domain_name" {
  description = "Domain name for the website (leave empty to skip Route 53 setup)"
  type        = string
  default     = ""
}

variable "content_refresh_hours" {
  description = "Hours between content refreshes"
  type        = number
  default     = 24
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "vex5hub-site"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

variable "season_id" {
  description = "RobotEvents Season ID (197 for 2025-2026). USER MUST VERIFY THIS ID."
  type        = number
  default     = 197
}
