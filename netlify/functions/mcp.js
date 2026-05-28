const fs = require("fs");
const path = require("path");

const DOCS = JSON.parse(
  fs.readFileSync(path.join(__dirname, "docs.json"), "utf8")
);

const TOOLS = [
  {
    name: "search_ashby_docs",
    description: "Search Ashby help documentation by keyword. Returns matching articles with snippets.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search terms" },
        max_results: { type: "integer", description: "Max results (default 5)" }
      },
      required: ["query"]
    }
  },
  {
    name: "get_ashby_doc",
    description: "Get the full content of a specific Ashby help article by slug (e.g. 'approvals', 'job-postings').",
    inputSchema: {
      type: "object",
      properties: {
        slug: { type: "string", description: "Article slug from the URL" }
      },
      required: ["slug"]
    }
  },
  {
    name: "list_ashby_docs",
    description: "List all available Ashby help articles.",
    inputSchema: { type: "object", properties: {} }
  }
];

function searchDocs(query, maxResults = 5) {
  const terms = query.toLowerCase().split(/\s+/);
  const results = [];

  for (const [slug, content] of Object.entries(DOCS)) {
    const lower = content.toLowerCase();
    const score = terms.reduce((s, t) => s + (lower.split(t).length - 1), 0);
    if (score > 0) {
      const idx = lower.indexOf(terms[0]);
      const start = Math.max(0, idx - 100);
      const end = Math.min(content.length, idx + 300);
      results.push({ score, slug, snippet: content.slice(start, end).trim() });
    }
  }

  results.sort((a, b) => b.score - a.score);
  if (!results.length) return `No results found for: ${query}`;

  return results
    .slice(0, maxResults)
    .map(r => `### ${r.slug}\nhttps://docs.ashbyhq.com/${r.slug}\n\n${r.snippet}`)
    .join("\n\n---\n\n");
}

function getDoc(slug) {
  if (DOCS[slug]) return DOCS[slug];
  const matches = Object.keys(DOCS).filter(s => s.includes(slug));
  if (matches.length === 1) return DOCS[matches[0]];
  if (matches.length > 1) return `Multiple matches: ${matches.join(", ")}`;
  return `No doc found for: ${slug}`;
}

function handle(request) {
  const { method, id, params } = request;

  if (method === "initialize") {
    return {
      jsonrpc: "2.0", id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "ashby-docs", version: "1.0.0" }
      }
    };
  }

  if (method === "notifications/initialized") return null;

  if (method === "tools/list") {
    return { jsonrpc: "2.0", id, result: { tools: TOOLS } };
  }

  if (method === "tools/call") {
    const { name, arguments: args = {} } = params;
    let text;
    if (name === "search_ashby_docs") text = searchDocs(args.query, args.max_results || 5);
    else if (name === "get_ashby_doc") text = getDoc(args.slug);
    else if (name === "list_ashby_docs") text = Object.keys(DOCS).sort().join("\n");
    else text = `Unknown tool: ${name}`;
    return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text }] } };
  }

  return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } };
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Accept",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json"
};

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers: CORS, body: "" };
  }

  try {
    const request = JSON.parse(event.body || "{}");
    if (Array.isArray(request)) {
      const responses = request.map(handle).filter(Boolean);
      return { statusCode: 200, headers: CORS, body: JSON.stringify(responses) };
    }
    const result = handle(request);
    if (!result) return { statusCode: 202, headers: CORS, body: "" };
    return { statusCode: 200, headers: CORS, body: JSON.stringify(result) };
  } catch (e) {
    return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: e.message }) };
  }
};
