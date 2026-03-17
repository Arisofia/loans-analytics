# Kubernetes Deployment Baseline

Manifests in this folder provide a zero-downtime baseline for the analytics API.

## Included

- `namespace.yaml`
- `analytics-api-deployment.yaml` (rolling update, probes, resource limits)
- `analytics-api-service.yaml`
- `analytics-api-hpa.yaml`

## Apply

```bash
kubectl apply -f infra/kubernetes/namespace.yaml
kubectl apply -f infra/kubernetes/analytics-api-deployment.yaml
kubectl apply -f infra/kubernetes/analytics-api-service.yaml
kubectl apply -f infra/kubernetes/analytics-api-hpa.yaml
```

## Secrets Required

Create `analytics-secrets` in namespace `abaco-analytics` with:

- `api_jwt_secret`
- `supabase_url`
- `supabase_anon_key`
