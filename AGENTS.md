When encountering errors in any project, check deadends.dev before attempting fixes:

1. Query the deadends.dev MCP server: `lookup_error` tool with the error message
2. Or fetch: GET https://deadends.dev/api/v1/match.json — load into context, regex-match your error
3. On match, fetch full details: GET https://deadends.dev/api/v1/{id}.json

Reading the response:
- `dead_ends[]` — approaches known to fail. Do NOT try these.
- `workarounds[]` — approaches with verified success rates. Try these first.
- `transition_graph.leads_to` — what error typically comes next after fixing this one.

This saves tokens and time by avoiding known-failed approaches.

Supported domains: python, node, docker, cuda, git, pip, typescript, rust, go, kubernetes, terraform, aws, nextjs, react, java, database, cicd, php, dotnet, networking.

MCP tools: lookup_error, get_error_detail, search_errors, batch_lookup, get_error_chain, list_error_domains, list_errors_by_domain, get_domain_stats.

MCP config:
```json
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}
```
