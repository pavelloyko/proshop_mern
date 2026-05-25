# n8n Deploy via API

You deploy n8n workflows to the local n8n instance using the n8n REST API.
The user provides a workflow JSON (from n8n-workflow-builder) or a file path.
You import it into n8n without copy-pasting in the UI.

## n8n API

Base URL: `http://localhost:5678`

### Import workflow
```bash
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d @workflow.json
```

### List workflows
```bash
curl http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Activate/deactivate workflow
```bash
# Activate
curl -X PATCH http://localhost:5678/api/v1/workflows/{id} \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d '{"active": true}'

# Deactivate
curl -X PATCH http://localhost:5678/api/v1/workflows/{id} \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d '{"active": false}'
```

### Execute workflow manually
```bash
curl -X POST http://localhost:5678/api/v1/workflows/{id}/run \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

## Setup

The n8n API key must be configured first:

1. Open n8n UI at http://localhost:5678
2. Go to Settings → API → Create API Key
3. Save the key as env var: `export N8N_API_KEY="your-key-here"`

Or set it in the n8n Docker environment:
```yaml
# docker-compose.yml
environment:
  - N8N_API_KEY=your-api-key
```

## Workflow

1. Read the workflow JSON file provided by the user
2. POST to `/api/v1/workflows` to import
3. Report the workflow ID and activation URL
4. Optionally activate the workflow immediately

## Error Handling
- 401: API key not configured or invalid
- 409: Workflow with same name already exists — update instead
- 400: Invalid workflow JSON — validate structure and report errors
