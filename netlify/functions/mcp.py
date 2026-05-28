import json
import os

DOCS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs.json")

with open(DOCS_FILE) as f:
    DOCS = json.load(f)

TOOLS = [
    {
        "name": "search_ashby_docs",
        "description": "Search Ashby help documentation by keyword. Returns matching articles with snippets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_ashby_doc",
        "description": "Get the full content of a specific Ashby help article by slug (e.g. 'approvals', 'job-postings').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Article slug from the URL"}
            },
            "required": ["slug"]
        }
    },
    {
        "name": "list_ashby_docs",
        "description": "List all available Ashby help articles.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

def search_docs(query, max_results=5):
    terms = query.lower().split()
    results = []
    for slug, content in DOCS.items():
        lower = content.lower()
        score = sum(lower.count(t) for t in terms)
        if score > 0:
            idx = lower.find(terms[0])
            start, end = max(0, idx - 100), min(len(content), idx + 300)
            results.append((score, slug, content[start:end].strip()))
    results.sort(reverse=True)
    if not results:
        return f"No results found for: {query}"
    out = []
    for _, slug, snippet in results[:max_results]:
        out.append(f"### {slug}\nhttps://docs.ashbyhq.com/{slug}\n\n{snippet}")
    return "\n\n---\n\n".join(out)

def get_doc(slug):
    if slug in DOCS:
        return DOCS[slug]
    matches = [s for s in DOCS if slug in s]
    if len(matches) == 1:
        return DOCS[matches[0]]
    if len(matches) > 1:
        return f"Multiple matches: {', '.join(matches)}"
    return f"No doc found for: {slug}"

def handle(request):
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ashby-docs", "version": "1.0.0"}
            }
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = request["params"]["name"]
        args = request["params"].get("arguments", {})
        if name == "search_ashby_docs":
            text = search_docs(args["query"], args.get("max_results", 5))
        elif name == "get_ashby_doc":
            text = get_doc(args["slug"])
        elif name == "list_ashby_docs":
            text = "\n".join(sorted(DOCS.keys()))
        else:
            text = f"Unknown tool: {name}"
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": text}]}
        }

    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Accept",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json"
}

def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        body = event.get("body") or ""
        request = json.loads(body)

        # Handle batch requests
        if isinstance(request, list):
            responses = [r for r in (handle(r) for r in request) if r is not None]
            return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(responses)}

        result = handle(request)
        if result is None:
            return {"statusCode": 202, "headers": CORS_HEADERS, "body": ""}
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(result)}

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }
