# API Architecture

## Overview

REST API built with FastAPI (Python). Stateless design — no server-side sessions.

## Layers

```
Client → API Gateway → Auth → Route Handler → Service → [[Database Design]]
```

## Design principles

- **Stateless:** All state in [[JWT]] tokens or database
- **Versioned:** `/api/v1/` prefix for all routes
- **Documented:** OpenAPI spec auto-generated
- **Validated:** Request/response schemas enforced

## Rate limiting

- 100 requests per minute per IP
- 1000 requests per minute per authenticated user
- Applied at API gateway level

## Error handling

- Consistent error format: `{ "error": { "code": "...", "message": "..." } }`
- HTTP status codes follow REST conventions
- No stack traces in production responses

## Related

- [[Auth Design]] — authentication layer
- [[Database Design]] — data layer
- [[Deployment Strategy]] — how the API is deployed
- [[Performance Tuning]] — optimization
