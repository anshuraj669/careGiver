# CareCircle

A voice-first eldercare companion for Alexa+, built as a self-hosted **MCP server (protocol 2025-11-25)**.
It helps an older adult who lives alone manage medications, avoid scams and stay connected to family,
and keeps the family caregiver informed.

## Quick start

```bash
uv sync
uv run carecircle                         # MCP endpoint at http://127.0.0.1:8000/mcp
uv run python scripts/demo_client.py      # in another terminal: walk through demo scenarios
uv run pytest                             # unit + end-to-end MCP tests
```

The first run seeds a demo household (Margaret, 78, and her daughter Priya) with a week of dose
history. Reset it any time with `uv run carecircle --seed`.

Inspect it interactively with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector      # transport: Streamable HTTP, URL: http://127.0.0.1:8000/mcp
```

## MCP surface

| Tools | What it does |
|---|---|
| `get_medication_schedule` | Today's doses with status (taken / due / missed / upcoming); ask about one med by name or purpose |
| `log_medication_dose` | Logs a dose, with a **double-dose guard** |
| `add_medication` | Adds a prescription |
| `check_for_scam` | Elder-fraud red-flag check; alerts family on high risk |
| `daily_check_in` | Mood and symptoms; escalates falls, dizziness and chest pain |
| `notify_caregiver` | Sends a message to the caregiver |
| `emergency_help` | Sends an urgent alert immediately |
| `get_care_summary` | Adherence stats plus a written weekly summary |
| `request_pharmacy_refill` | Orders a refill; runs as an async **task** with progress updates |

**Resources:** `care://profile`, `care://medications`, `care://today`, `care://alerts`, `care://refills`.
**Prompts:** `morning_check_in`, `weekly_caregiver_report`.
Every tool has annotations, a title, an icon and an `outputSchema`, and returns `structuredContent`.

**2025-11-25 spec features:**

- **Tasks:** `request_pharmacy_refill` declares `execution.taskSupport: "optional"`. Call it with a
  `task` field and poll `tasks/get` to watch it move from requested to ready. A plain call finishes at once.
- **Elicitation:** `notify_caregiver` asks the person to confirm before it messages family. Clients
  without elicitation send as asked. Scam and emergency alerts never ask, because scammers push secrecy.
- **Icons:** on the server, every tool, every resource and every prompt.
- **OAuth 2.1:** set `OAUTH_ISSUER` (Amazon Cognito) and `/mcp` requires a bearer JWT. The server
  publishes `/.well-known/oauth-protected-resource/mcp` and answers 401 with a `WWW-Authenticate`
  challenge. It checks signature, expiry, issuer, audience and scopes.

## Configuration

See `.env.example`. Everything runs offline with `LLM_PROVIDER=none` (rule-based scam detection
and template summaries). Set `LLM_PROVIDER=bedrock` to use Claude on Amazon Bedrock.

## Layout

```
src/carecircle/
  app.py          HTTP entry point (Starlette + uvicorn), /mcp and /health
  mcp_server.py   MCP tools, resources, prompts, task-augmented tool calls
  auth.py         OAuth 2.1 resource server: JWT verification against Cognito
  icons.py        SVG icons for tools, resources and prompts
  service.py      care logic (schedule, dose guard, alerts, check-ins, summaries)
  scam.py         fraud red-flag rules + optional Claude refinement
  store.py        JSON-file or DynamoDB document store
  llm.py          Claude via Bedrock (Mantle) or the Claude API
  notify.py       caregiver SMS via Amazon SNS
  seed.py         demo household
```

## Roadmap

Details and the AWS services per phase are in [PHASES.md](PHASES.md).

- [x] **Phase 1:** core MCP server, tools, resources and prompts, tests
- [x] **Phase 2:** Tasks (async pharmacy refill), elicitation (confirm before messaging family), icons, OAuth 2.1
- [ ] **Phase 3:** Alexa+-style voice simulator web app with a Claude agent
- [ ] **Phase 4:** caregiver dashboard, missed-dose and inactivity scheduler, SNS SMS
- [ ] **Phase 5:** AWS deployment (DynamoDB, Docker, CDK)
- [ ] **Phase 6:** demo polish (architecture diagram, spec-compliance table, demo script)
