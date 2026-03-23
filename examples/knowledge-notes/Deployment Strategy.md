# Deployment Strategy

## Overview

Containerized deployment with Docker. Each service runs in its own container.

## Architecture

```
Load Balancer (Nginx)
    ├── API Container 1
    ├── API Container 2
    └── API Container 3
          │
          ▼
    PostgreSQL (managed)
```

## CI/CD

1. Push to main branch
2. GitHub Actions runs tests
3. Build Docker image
4. Push to container registry
5. Deploy to production (rolling update)

## Environments

- **Development:** Local Docker Compose
- **Staging:** Same as production, smaller scale
- **Production:** 3 API containers, managed PostgreSQL

## Database deployment

- [[Migrations]] run as part of deployment pipeline
- Rollback: `alembic downgrade -1` before redeploying old code
- Blue-green deployment for zero-downtime updates

## Related

- [[API Architecture]] — what's being deployed
- [[Database Design]] — how the database is deployed
- [[Migrations]] — schema changes in deployment
- [[Auth Design]] — how auth works across environments
