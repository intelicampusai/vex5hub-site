variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ca-central-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "nighthawks"
}

variable "domain_name" {
  description = "Domain name for the website (leave empty to skip Route 53 setup)"
  type        = string
  default     = ""
}

variable "content_refresh_hours" {
  description = "Hours between content refreshes"
  type        = number
  default     = 4
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "3150N-Nighthawks"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

variable "season_id" {
  description = "RobotEvents Season ID (e.g. 190 for 2024-2025). USER MUST VERIFY THIS ID."
  type        = number
  default     = 190
}
