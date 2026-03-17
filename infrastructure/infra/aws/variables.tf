variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project identifier used for resource naming."
  type        = string
  default     = "abaco-loans-analytics"
}

variable "environment" {
  description = "Environment label."
  type        = string
  default     = "prod"
}

variable "tags" {
  description = "Additional AWS tags."
  type        = map(string)
  default     = {}
}
