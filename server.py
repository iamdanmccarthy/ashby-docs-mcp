#!/usr/bin/env python3.11
import os
import json
import sys

DOCS_DIR = os.path.expanduser("~/ashby_docs")

def load_docs():
    docs = {}
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".md"):
            slug = filename[:-3]
            filepath = os.path.join(DOCS_DIR, filename)
            with open(filepath, "r") as f:
                docs[slug] = f.read()
    return docs

DOCS = load_docs()

def search_docs(query: str, max_results: int = 5) -> str:
    query_terms = query.lower().split()
    results = []

    for slug, content in DOCS.items():
        content_lower = content.lower()
        score = sum(content_lower.count(term) for term in query_terms)
        if score > 0:
            # Find a snippet around the first match
            first_term = query_terms[0]
            idx = content_lower.find(first_term)
            start = max(0, idx - 100)
            end = min(len(content), idx + 300)
            snippet = content[start:end].strip()
            results.append((score, slug, snippet))

    results.sort(reverse=True)
    results = results[:max_results]

    if not results:
        return f"No results found for: {query}"

    output = []
    for score, slug, snippet in results:
        url = f"https://docs.ashbyhq.com/{slug}"
        output.append(f"### {slug}\n{url}\n\n{snippet}\n")

    return "\n---\n".join(output)

def get_doc(slug: str) -> str:
    if slug in DOCS:
        return DOCS[slug]
    # Try partial match
    matches = [s for s in DOCS if slug in s]
    if len(matches) == 1:
        return DOCS[matches[0]]
    elif len(matches) > 1:
        return f"Multiple matches: {', '.join(matches)}"
    return f"No doc found for: {slug}"

def list_docs() -> str:
    slugs = sorted(DOCS.keys())
    return "\n".join(slugs)

# MCP protocol over stdio
def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def handle(request):
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        send({
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ashby-docs", "version": "1.0.0"}
            }
        })

    elif method == "tools/list":
        send({
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": [
                {
                    "name": "search_ashby_docs",
                    "description": "Search Ashby help documentation by keyword. Returns matching articles with snippets.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search terms"},
                            "max_results": {"type": "integer", "description": "Max results to return (default 5)"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_ashby_doc",
                    "description": "Get the full content of a specific Ashby help article by its slug (e.g. 'approvals', 'job-postings').",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "slug": {"type": "string", "description": "Article slug from the URL, e.g. 'approvals'"}
                        },
                        "required": ["slug"]
                    }
                },
                {
                    "name": "list_ashby_docs",
                    "description": "List all available Ashby help articles.",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]}
        })

    elif method == "tools/call":
        name = request["params"]["name"]
        args = request["params"].get("arguments", {})

        if name == "search_ashby_docs":
            result = search_docs(args["query"], args.get("max_results", 5))
        elif name == "get_ashby_doc":
            result = get_doc(args["slug"])
        elif name == "list_ashby_docs":
            result = list_docs()
        else:
            result = f"Unknown tool: {name}"

        send({
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": result}]}
        })

    elif method == "notifications/initialized":
        pass  # No response needed

    else:
        send({
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        })

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            handle(request)
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
