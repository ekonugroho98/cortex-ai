# Claude Code CLI Setup Guide

This guide explains how to setup and configure Claude Code CLI with Z.ai GLM models for the BigQuery AI Service.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WEB INTERFACE                        │
│  (Browser with chat UI)                                 │
└────────────────┬────────────────────────────────────────┘
                    │ WebSocket / HTTP
                    ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                   │
│  - Spawns Claude Code CLI as subprocess                 │
│  - Sends prompts via stdin                              │
│  - Receives responses via stdout                        │
└────────────────┬────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│         CLAUDE CODE CLI (Subprocess)                    │
│  - Installed via npm                                    │
│  - Configured with Z.ai GLM models                      │
│  - Executes prompts and returns results                 │
└────────────────┬────────────────────────────────────────┘
                    ↓
         Zhipu AI / Anthropic API
```

## Prerequisites

1. **Node.js 18+**
   ```bash
   node --version  # Should be v18 or higher
   ```

2. **Z.ai API Key**
   - Sign up at: https://open.bigmodel.cn/
   - Get your API key from the console

3. **Claude Code CLI**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

## Installation Steps

### 1. Install Claude Code CLI

```bash
# Install globally via npm
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

Expected output:
```
2.0.14 (Claude Code)
```

### 2. Configure Z.ai GLM Models

Claude Code CLI uses the `~/.claude/settings.json` file to configure models.

Create or edit `~/.claude/settings.json`:

```bash
# Create config directory
mkdir -p ~/.claude

# Create settings file
cat > ~/.claude/settings.json << 'EOF'
{
  "env": {
    "ANTHROPIC_API_KEY": "YOUR_ZHIPU_AI_API_KEY",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.7"
  }
}
EOF
```

**Important**: Replace `YOUR_ZHIPU_AI_API_KEY` with your actual Z.ai API key.

### 3. Set Environment Variable (Alternative)

Alternatively, you can set the API key as an environment variable:

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY="your-zhipu-ai-api-key"

# Reload shell
source ~/.bashrc
```

### 4. Test Claude Code CLI

```bash
# Test basic functionality
echo "What is 2+2?" | claude --print

# Test with BigQuery context
cd /path/to/bigquery/claude-workspace
echo "Generate a BigQuery query to select all users" | claude --print
```

## Model Configuration

The following Z.ai GLM models are supported:

| Model | Usage | Description |
|-------|-------|-------------|
| `glm-4.7` | Default | Most capable model for complex tasks |
| `glm-4.5-air` | Fast | Faster model for simple tasks |

### Model Selection

Claude Code CLI automatically selects the model based on task complexity:

- **Haiku** (glm-4.5-air): Fast, simple queries
- **Sonnet** (glm-4.7): Balanced performance
- **Opus** (glm-4.7): Maximum capability

## How It Works

### 1. Subprocess Execution

The FastAPI service spawns Claude Code CLI as a subprocess:

```python
process = await asyncio.create_subprocess_exec(
    "claude",
    "--print",  # Print output to stdout
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    cwd="/path/to/workspace"
)

# Send prompt
process.stdin.write(prompt.encode())
process.stdin.close()

# Read response
output = process.stdout.read()
```

### 2. Prompt Engineering

The service constructs prompts with BigQuery context:

```
You are a BigQuery SQL expert. Your task is to help users generate optimized BigQuery SQL queries.

Available BigQuery Resources:
- Dataset: analytics
  - Table: my-project.analytics.users
    Columns: user_id (INT64), email (STRING), created_at (TIMESTAMP)
  - Table: my-project.analytics.orders
    Columns: order_id (INT64), user_id (INT64), amount (FLOAT64)

User Request:
Show me top 10 users by revenue

Expected Output Format:
```sql
SELECT ...
FROM `project.dataset.table`
```
```

### 3. Response Parsing

The service extracts SQL from Claude CLI output:

```python
# Parse code blocks
sql_pattern = r'```sql\n(.*?)\n```'
sql_matches = re.findall(sql_pattern, output, re.DOTALL)

if sql_matches:
    generated_sql = sql_matches[0].strip()
```

## Usage Examples

### HTTP Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me top 10 users by revenue",
    "dataset_id": "analytics",
    "dry_run": false
  }'
```

Response:
```json
{
  "status": "success",
  "prompt": "Show me top 10 users by revenue",
  "generated_sql": "SELECT user_id, SUM(amount) as total_revenue FROM ...",
  "execution_result": {
    "data": [...],
    "row_count": 10
  },
  "agent_metadata": {
    "model": "glm-4.7",
    "method": "claude-code-cli",
    "workspace": "/app/claude-workspace"
  }
}
```

### WebSocket Endpoint

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/agent');

ws.onopen = () => {
  // Configure session
  ws.send(JSON.stringify({
    type: 'configure',
    project_id: 'my-project',
    dataset_id: 'analytics'
  }));

  // Send prompt
  ws.send(JSON.stringify({
    type: 'prompt',
    prompt: 'Show me monthly revenue trend'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};
```

## Workspace Structure

Claude Code CLI requires a workspace with context files:

```
claude-workspace/
├── .claude/
│   └── settings.json          # Claude CLI config
└── bigquery_context/
    ├── schemas.md             # Dataset and table schemas
    ├── examples.md            # SQL query examples
    └── conventions.md         # SQL conventions
```

These files are automatically generated by the service when a request is made.

## Troubleshooting

### Claude CLI Not Found

```bash
# Check if claude is in PATH
which claude

# If not found, reinstall
npm install -g @anthropic-ai/claude-code

# Add npm global bin to PATH
export PATH="$PATH:$(npm config get prefix)/bin"
```

### API Key Not Working

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Check settings file
cat ~/.claude/settings.json

# Test with direct API call
curl https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4","messages":[{"role":"user","content":"Hello"}]}'
```

### Timeout Errors

Increase timeout in `.env`:

```bash
# Increase from default 300s to 600s
CLAUDE_TIMEOUT=600
```

### Permission Errors

Ensure the workspace directory is writable:

```bash
mkdir -p claude-workspace
chmod 755 claude-workspace
```

## Security Considerations

1. **API Key Protection**
   - Never commit `.claude/settings.json` to git
   - Use environment variables in production
   - Rotate API keys regularly

2. **Sandboxing**
   - Run Claude CLI in isolated environment
   - Limit filesystem access
   - Monitor subprocess execution

3. **Rate Limiting**
   - Implement rate limiting on API endpoints
   - Monitor API usage
   - Set budget limits in Z.ai console

## Performance Tips

1. **Cache Context**: The service caches BigQuery schema to avoid repeated API calls

2. **Parallel Execution**: For multiple independent queries, use WebSocket connections

3. **Timeout Management**: Set appropriate timeouts based on query complexity

4. **Model Selection**: Use `glm-4.5-air` for simple queries to reduce latency

## References

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/overview)
- [Z.ai Developer Docs](https://open.bigmodel.cn/dev/api)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)

## Next Steps

1. ✅ Install Claude Code CLI
2. ✅ Configure Z.ai GLM models
3. ✅ Test with simple prompts
4. 🔄 Integrate with BigQuery AI Service
5. 🔄 Deploy to production
