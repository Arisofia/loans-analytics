# AWS Terraform Starter

This folder adds an AWS deployment option without changing the existing Azure path.

## What It Provisions

- `aws_ecr_repository.analytics_api` for container images
- `aws_ecs_cluster.analytics` as the base runtime cluster

## Usage

```bash
cd infra/aws
terraform init
terraform plan -var "project_name=abaco-loans-analytics" -var "aws_region=us-east-1"
terraform apply -var "project_name=abaco-loans-analytics" -var "aws_region=us-east-1"
```

## Required Credentials

Use standard AWS auth (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN`) or an assumed role.

## Notes

- This is intentionally minimal and safe to validate in CI.
- Extend with VPC, ALB, ECS services, and RDS according to production requirements.
