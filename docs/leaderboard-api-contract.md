# Betterburn Leaderboard API Contract

This document defines the minimal HTTP contract Betterburn expects from a leaderboard API.

## Transport rules

- Protocol: HTTP
- Content type: JSON
- Request correlation: clients may send `X-Request-ID`; the server may echo it back or generate one
- Error envelope:

```json
{
  "error": "string"
}
```

## Authentication

- If the server is configured without an API key, auth may be disabled.
- If auth is enabled, every endpoint except `GET /healthz` must accept:

```http
Authorization: Bearer <API_KEY>
```

- Expected auth failure:
  - Status: `401`
  - Body:

```json
{
  "error": "Unauthorized"
}
```

## Identifier rules

### Steam ID

Betterburn expects Steam IDs as strings of exactly 17 digits.

Validation failure should return:
- Status: `400`
- Body:

```json
{
  "error": "steam_id must be a 17-digit number"
}
```

## Required endpoints

### 1. Health check

#### Request

- Method: `GET`
- Path: `/healthz`
- Auth: not required

#### Success response

- Status: `200`
- Body schema:

```json
{
  "status": "ok",
  "authenticated": true
}
```

#### Minimum field contract

- `status`: string
- `authenticated`: boolean

---

### 2. Single-user leaderboard standing

This is the primary read path Betterburn uses for rank lookup.

#### Request

- Method: `GET`
- Path: `/leaderboard`
- Query:
  - `sid=<17-digit steam id>`
- Auth: required when API key auth is enabled

#### Constraints

When `sid` is present, it must not be combined with:
- `limit`
- `cursor`
- `mapped`

#### Success response

- Status: `200`
- Body schema:

```json
{
  "steam_id": "76561198000000000",
  "stat_value": 1542,
  "position": 42,
  "timestamp": "2026-03-11T12:34:56+00:00"
}
```

#### Minimum field contract

- `steam_id`: string
- `stat_value`: integer
- `position`: integer
- `timestamp`: string in ISO 8601 datetime form

#### Not found cases

If the user cannot be resolved, or no leaderboard row exists yet:
- Status: `404`
- Body:

```json
{
  "error": "string"
}
```

---

### 3. Create or confirm Steam mapping

Betterburn uses this after account linking.

#### Request

- Method: `POST`
- Path: `/mappings`
- Auth: required when API key auth is enabled
- Content-Type: `application/json`
- Body schema:

```json
{
  "steam_id": "76561198000000000"
}
```

#### Success response

- Status: `201`
- Body schema:

```json
{
  "steam_id": "76561198000000000",
}
```

#### Minimum field contract

- `steam_id`: string

#### Validation failures

Missing field:
- Status: `422`

```json
{
  "error": "Missing required field: steam_id"
}
```

Invalid field format:
- Status: `400`

```json
{
  "error": "steam_id must be a 17-digit number"
}
```

## Compatible but optional endpoints

These are compatible with the upstream API shape but are not currently required for Betterburn's core link-and-verify flow.

### Leaderboard list mode

#### Request

- Method: `GET`
- Path: `/leaderboard`
- Query:
  - optional `mapped=true|false`
  - optional `limit`
  - optional `cursor`

#### Success response

```json
{
  "entries": [
    {
      "steam_id": "string|null",
      "stat_value": 1542,
      "position": 42
    }
  ],
  "next_cursor": "string|null",
  "has_more": true
}
```

### User history

#### Request

- Method: `GET`
- Path: `/history`
- Query:
  - required `sid=<17-digit steam id>`
  - optional `limit`

#### Success response

```json
{
  "steam_id": "76561198000000000",
  "entries": [
    {
      "timestamp": "2026-03-11T12:34:56+00:00",
      "elo": 1542
    }
  ]
}
```

## Opaque compatibility notes

A leaderboard API is considered Betterburn-compatible if it satisfies all of the following:
- Exposes `GET /healthz`
- Exposes `GET /leaderboard?sid=<steam_id>` with the exact minimum fields documented above
- Exposes `POST /mappings` with the exact minimum fields documented above
- Uses JSON error bodies with an `error` string
- Accepts bearer auth on protected routes when auth is enabled
- Treats Steam IDs as 17-digit strings

Anything beyond this contract is implementation detail and should be treated as opaque by Betterburn.
