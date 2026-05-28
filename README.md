# Ashby Docs MCP

A Model Context Protocol (MCP) server that makes all 215 Ashby help articles searchable by AI assistants.

## Add to Claude Code

```json
"ashby-docs": {
  "type": "http",
  "url": "https://ashby-docs-mcp.netlify.app/mcp"
}
```

## Tools

- `search_ashby_docs` — keyword search across all articles
- `get_ashby_doc` — fetch a full article by slug (e.g. `approvals`)
- `list_ashby_docs` — list all available articles

## Refresh the docs

```bash
python3 scrape_ashby.py       # re-scrape docs.ashbyhq.com
python3 build_docs.py         # rebuild docs.json
git add netlify/functions/docs.json && git commit -m "refresh docs"
git push
```
