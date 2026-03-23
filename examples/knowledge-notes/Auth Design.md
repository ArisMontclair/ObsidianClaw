# Auth Design

## Approach

Stateless authentication using [[JWT]] tokens. No server-side sessions.

## Flow

1. User logs in with email/password
2. Server validates credentials against [[Database Design]]
3. Server issues JWT access token (15 min) + refresh token (7 days)
4. Client stores tokens in httpOnly cookies
5. Subsequent requests include access token in Authorization header
6. When access token expires, client uses refresh token to get new one

## Security

- Passwords hashed with bcrypt (cost factor 12)
- Refresh tokens stored in database (revocable)
- Access tokens are stateless (no database lookup)
- CORS restricted to known frontend domains

## Token structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "iat": 1710000000,
  "exp": 1710000900,
  "role": "user"
}
```

## Related

- [[JWT]] — token implementation
- [[API Architecture]] — how auth integrates with API
- [[Database Design]] — where user data lives
- [[Deployment Strategy]] — how auth fits into deployment
