# Connect the toolkit to ChatGPT

ChatGPT cannot connect directly to the local stdio process. Run the Streamable HTTP MCP server on a URL ChatGPT can reach.

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev,docx,pdf]"
borealis-mcp-http
```

The MCP endpoint is normally available at:

```text
http://localhost:8000/mcp
```

For a local/private server, use a secure tunnel supported by your ChatGPT setup or deploy the container behind HTTPS. Do not expose an unauthenticated development server publicly.

## ChatGPT setup

1. Open ChatGPT **Settings → Apps**.
2. Enable **Developer mode** under advanced app settings when available for your plan/workspace.
3. Create a custom app and enter the public HTTPS MCP endpoint, ending in `/mcp`.
4. Review the tools and test prompts such as:
   - “Search Borealis for dementia datasets from University of Toronto.”
   - “Tell me more about the first dataset and preserve its DOI.”
   - “List CSV files in that dataset.”

The exact menus and plan availability can change. Consult current OpenAI documentation when deploying.
