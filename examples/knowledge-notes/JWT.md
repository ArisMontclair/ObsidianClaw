# JWT

## Structure

Three parts separated by dots:
- **Header:** Algorithm and token type
- **Payload:** Claims (user data, expiration)
- **Signature:** HMAC-SHA256 of header + payload + secret

## Implementation

```python
import jwt

# Create token
token = jwt.encode(
    {"sub": user_id, "exp": datetime.utcnow() + timedelta(minutes=15)},
    SECRET_KEY,
    algorithm="HS256"
)

# Verify token
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

## Best practices

- **Short-lived access tokens:** 15 minutes
- **Long-lived refresh tokens:** 7 days, stored in database
- **Rotate refresh tokens:** New refresh token on each use
- **Blacklist compromised tokens:** Store in Redis, check on every request

## Related

- [[Auth Design]] — how JWT fits into authentication
- [[API Architecture]] — how tokens are used in API
- [[Connection Pooling]] — how JWT validation connects to database
