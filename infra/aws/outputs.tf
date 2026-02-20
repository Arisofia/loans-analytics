output "ecr_repository_url" {
  description = "ECR URL for analytics API images."
  value       = aws_ecr_repository.analytics_api.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name for analytics workloads."
  value       = aws_ecs_cluster.analytics.name
}
