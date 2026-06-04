# Week 14 Operations Assistant

AI-powered operations assistant for a small electronics store. A **FastMCP** server exposes inventory and document tools; a **CrewAI** crew (three agents) answers one operations question per run, cites sources, saves a markdown report, and records full execution traces.

Example outputs from real runs are documented in **[SAMPLE_RESPONSES.md](SAMPLE_RESPONSES.md)**.

---

## What it does

| Component | Purpose |
|-----------|---------|
| **MCP server** (`mcp_server/`) | Tools: `read_inventory`, `search_documents`, `read_documents`, `save_report`, `ping` |
| **Crew** (`crew/`) | Research → analyze → save report for a single natural-language query |
| **Dashboard** (`dashboard/`) | Streamlit UI: answer, proof (source files), and per-tool trace |
| **Data** (`data/`) | `inventory.csv` + policy/product/support `.txt` documents |
| **Outputs** | `reports/*.md` (saved reports), `traces/crew_run_*.json` (full run payloads) |

### Agent workflow (sequential)

1. **Inventory Research Specialist** — Calls MCP: inventory + document search/read  
2. **Operations Analyst** — Synthesizes research into an answer with citations  
3. **Report Writer** — Calls MCP `save_report` to write `reports/<name>.md`

---

## Requirements

- **Python 3.12** (required; CrewAI/chromadb are not reliable on 3.14)
- **Groq API key** — [console.groq.com](https://console.groq.com/)
- Optional: [uv](https://github.com/astral-sh/uv) for fast installs (or use `pip`)

---

## Clone and run (quick start)

### 1. Clone the repository

```bash
git clone <your-repo-url> week-14-operations-assistant
cd week-14-operations-assistant
```

### 2. Create a virtual environment (Python 3.12)

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

If you use [pyenv](https://github.com/pyenv/pyenv), the repo includes `.python-version` (`3.12`).

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

With uv:

```bash
uv pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # macOS / Linux
```

Edit `.env` and set your Groq key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Optional variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_MODEL` | `groq/llama-3.3-70b-versatile` | LiteLLM model id |
| `GROQ_TEMPERATURE` | `0.2` | Sampling temperature |
| `CREWAI_TRACING_ENABLED` | `true` | CrewAI tracing |
| `OPERATIONS_STREAMLIT_PORT` | `8502` | Dashboard port |
| `CREW_PYTHON` | current `python` | Python used to spawn MCP stdio server |

**Never commit `.env`** — it is listed in `.gitignore`.

### 5. Run the crew (CLI)

Default question (reorder + suppliers):

```bash
python run_crew.py
```

Custom question:

```bash
python run_crew.py "Which products need reordering?"
```

On success you will see:

- Printed **answer** in the terminal  
- Path to a **report** under `reports/`  
- Path to a **trace** under `traces/crew_run_<timestamp>.json`

### 6. Run the Streamlit dashboard (optional)

```bash
python run_dashboard.py
```

Open **http://localhost:8502** (default). Use the **Ask** tab to run a query; view answer, proof, and tool traces. Use **History** to reload past `traces/crew_run_*.json` files.

**Not MarketMind:** If another Streamlit app (e.g. MarketMind) runs on port **8501**, do not open that tab for this project. Always use **8502** and look for the green banner **Week 14 Operations Inventory Assistant**.

On Windows, if `streamlit.exe` is blocked by policy, `run_dashboard.py` uses `python -m streamlit` instead. Always launch via `python run_dashboard.py` from this repo root (not `streamlit run` without `--server.port 8502`).

Change port:

```powershell
$env:OPERATIONS_STREAMLIT_PORT = "8503"
python run_dashboard.py
```

```bash
export OPERATIONS_STREAMLIT_PORT=8503
python run_dashboard.py
```

---

## Project structure

```
week-14-operations-assistant/
├── data/
│   ├── inventory.csv              # Product stock, reorder levels, suppliers
│   └── documents/                 # Policies, product notes, support tickets
├── mcp_server/
│   ├── server.py                  # FastMCP entry point
│   ├── tools.py                   # Tool implementations
│   ├── resources.py               # CSV / document I/O
│   └── schemas.py                 # Pydantic request/response models
├── crew/
│   ├── agents.py                  # Research, analyst, reporter agents
│   ├── tasks.py                   # Sequential task definitions
│   ├── crew.py                    # build_crew(), run_query(), trace save
│   ├── config.py                  # Paths, Groq LLM, MCP stdio config
│   └── tracing.py                 # Proof + tool-call collection
├── dashboard/
│   └── app.py                     # Streamlit UI
├── reports/                       # Generated markdown reports (git-tracked samples)
├── traces/                        # JSON traces per crew run
├── run_crew.py                    # CLI entry
├── run_dashboard.py               # Dashboard launcher
├── requirements.txt
├── .env.example
├── SAMPLE_RESPONSES.md            # Three documented system outputs
└── README.md
```

---

## MCP server (standalone)

The crew spawns the MCP server automatically over **stdio**. You can also run or inspect it directly.

**Install** (same venv as above):

```bash
pip install -r requirements.txt
```

**Stdio** (default for MCP clients):

```bash
fastmcp run mcp_server/server.py
```

**HTTP** (local testing):

```bash
fastmcp run mcp_server/server.py --transport http --port 8765
```

**Inspect / health check:**

```bash
fastmcp inspect mcp_server/server.py:mcp
fastmcp call --server-spec http://127.0.0.1:8765/mcp --target ping
```

### MCP tools

| Tool | Description |
|------|-------------|
| `read_inventory` | Load `data/inventory.csv`; optional `low_stock_only` filter |
| `search_documents` | Keyword search across `data/documents/*.txt` |
| `read_documents` | Full text of one `.txt` document by filename |
| `save_report` | Write markdown to `reports/` from title + content |
| `ping` | Server health check |

---

## Example questions

The crew accepts any operations question grounded in inventory and documents. Good starters:

```bash
python run_crew.py "Which products need reordering and which suppliers should be contacted?"
python run_crew.py "Which products need reordering?"
python run_crew.py "Summarize current inventory and flag low-stock items."
python run_crew.py "What does the return policy say about damaged goods?"
python run_crew.py "Are there open support tickets related to stock or shipping?"
```

See **[SAMPLE_RESPONSES.md](SAMPLE_RESPONSES.md)** for three full responses already produced by the system.

---

## Traces and proof

Each run writes:

- `traces/crew_run_<UTC>.json` — query, answer, tasks, `tool_calls`, `proof`, `events`  
- `traces/mcp_tools_<UTC>.jsonl` — MCP-side tool log (when `OPS_TRACE_PATH` is set)

The dashboard and trace JSON include **proof**: which CSV rows and document paths backed each tool result.

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `GROQ_API_KEY is not set` | Create `.env` from `.env.example` and set the key |
| Import / CrewAI errors on Python 3.14+ | Use Python **3.12** only |
| `litellm` / Groq errors | `pip install "crewai[litellm]"` |
| MCP document read fails | Only `.txt` files under `data/documents/` are supported |
| Dashboard port in use | Set `OPERATIONS_STREAMLIT_PORT` to another port |
| Windows `streamlit` blocked | Use `python run_dashboard.py` (not `streamlit.exe`) |

---

## License / attribution

Course project — Week 14 Operations Assistant. Adjust clone URL and license as needed for your fork.
