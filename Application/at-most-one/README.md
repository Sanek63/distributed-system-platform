## ServiceA

### `POST /api/message`

```bash
curl -X POST "http://localhost:10001/api/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
```

**Response (200):**
```json
{
  "status": "forwarded",
  "service_b_status_code": 200
}
```

---

## ServiceB

### `POST /api/message`

```bash
curl -X POST "http://localhost:10002/api/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
```

**Response (200):**
```json
{
  "status": "ok",
  "received": "hello"
}
```