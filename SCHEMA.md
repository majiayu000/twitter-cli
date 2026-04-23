# Structured Output Schema

`twitter-cli` uses a shared agent-friendly envelope for machine-readable output.

## Success

```yaml
ok: true
schema_version: "1"
data: ...
pagination:
  nextCursor: "optional-cursor"
```

## Error

```yaml
ok: false
schema_version: "1"
error:
  code: api_error
  message: User @foo not found
```

## Notes

- `--yaml` and `--json` both use this envelope
- non-TTY stdout defaults to YAML
- tweet and user lists are returned under `data`
- Explore commands return trend/news item lists under `data`
- timeline-style list commands may also return `pagination.nextCursor`
- `article` returns a single tweet object under `data`
- `status` returns `data.authenticated` plus `data.user`
- `whoami` returns `data.user`
- write commands also support explicit `--json` / `--yaml`

## Article Fields

`twitter article <id> --json` returns the standard tweet object plus:

```yaml
data:
  id: "1234567890"
  articleTitle: "Article Title"
  articleText: |
    # Heading
    Body text...
```

## Explore Fields

`twitter explore --section news --json` and `twitter today-news --json` return Explore
items:

```yaml
data:
  - id: "1234567890"
    name: "Topic title"
    section: news
    context: "4 hours ago · News · 195 posts"
    category: News
    timeContext: "4 hours ago"
    postCountText: "195 posts"
    url: "twitter://trending/1234567890"
    imageUrls: []
    isAiTrend: false
```

## Error Codes

Common structured error codes:

- `not_authenticated`
- `not_found`
- `invalid_input`
- `rate_limited`
- `api_error`
