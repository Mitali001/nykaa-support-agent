# Nykaa Domain Support Agent — CrewAI Capstone

**Track completed: Nykaa (E-commerce & Retail).** This repository implements the 16-task capstone brief. All customer/order data and policy text are fabricated for this educational project; these documents do **not** represent verified current Nykaa policy.

## Important execution modes

- `MOCK_LLM=true` is the graded/default mode. No hosted LLM, API key, or outbound LLM request is used.
- The local offline smoke suite was run in this build environment: core tests passed and all `run_all.py` demonstrations completed. Framework-specific tests are skipped here because CrewAI, AutoGen, ChromaDB, SentenceTransformers, and LangChain are not preinstalled in the build container; install the selected profile requirements and regenerate transcripts to verify those framework execution paths on your machine.
- CrewAI telemetry is disabled before Crew construction with `CREWAI_DISABLE_TELEMETRY=true` and `OTEL_SDK_DISABLED=true`.
- SentenceTransformers is used when its model is already cached locally. The first-time model download is a setup operation and requires internet; the offline fallback is deterministic feature hashing and is clearly reported in transcripts. To demonstrate the required SentenceTransformers path, pre-download/cache `sentence-transformers/all-MiniLM-L6-v2` before disconnecting from the network.
- ChromaDB creates two persistent collections (`nykaa_fixed_overlap`, `nykaa_sentence_chunks`) and uses `collection.upsert`. A JSON fallback is included only so unit/smoke tests can run without optional packages.
- CrewAI and AutoGen are runtime integrations. The Python 3.12 profile installs both; the Python 3.14 profile installs AutoGen but intentionally omits CrewAI because CrewAI currently excludes Python 3.14. The deterministic offline core remains runnable without CrewAI. Do not describe fallback execution as proof that the CrewAI integration was exercised; see `transcripts/` and `tests/test_optional_integrations.py`.

## Part 1 — reproducible dataset design (Task 1)

- Seed: `42`; records: `50`.
- Category weights in vocabulary order `[Apparel, Electronics, Home, Footwear, Beauty]`: `[20, 15, 15, 15, 35]`.
- Status weights in vocabulary order `[Placed, Shipped, Delivered, Returned, Refunded]`: `[15, 25, 35, 15, 10]`.
- Amount range: INR `199–14,999`; chosen to cover low-price beauty purchases through higher-priced electronics/home examples without claiming actual Nykaa transaction distributions.
- Delayed-shipment Bernoulli probability: `0.20`; the seed-42 run yields `10/50 = 20%`, validated to be within 10–30% (not hand-edited).
- Run `python -m dataset.dataset`; the script prints all counts and saves `dataset/orders.json`.

## Quick start — choose an installed Python version (Windows)

This project supports the two interpreters currently suitable from your installed list:

| Installed version | Project profile | CrewAI status | Recommendation |
|---|---|---|---|
| Python 3.12 (64-bit) | Full capstone: FastAPI, RAG, ChromaDB, SentenceTransformers, AutoGen and CrewAI | Supported by the selected CrewAI release | **Recommended for assignment submission** |
| Python 3.14 (64-bit) | Dashboard, API, RAG, ChromaDB, SentenceTransformers and AutoGen | CrewAI package is excluded; deterministic fallback is used | Use when you specifically need Python 3.14 |
| Python 3.9 / 3.8 | Not supported by this framework stack | Not supported | Do not use for this project |

**Important:** CrewAI's published package metadata currently specifies `Python >=3.10,<3.14`. Python 3.14 can run the rest of the app profile, but cannot run the real CrewAI integration. The 3.12 profile is therefore the correct choice when demonstrating every capstone requirement. See the [CrewAI Python requirement](https://github.com/crewAIInc/crewAI/blob/main/pyproject.toml) and [AutoGen AgentChat requirement](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/pyproject.toml).

### Easiest setup

1. Extract the ZIP and open the project folder in PyCharm.
2. Double-click `setup.bat`.
3. Choose **1 for Python 3.12** (recommended) or **2 for Python 3.14**.
4. The script creates an isolated `.venv312` or `.venv314` environment and installs the matching requirements file.
5. Double-click `start_app.bat` and choose the same environment.
6. Open **http://127.0.0.1:8000/ (dashboard; aliases: /dashboard and /index.html)**.

You can keep both environments side by side; they do not overwrite one another. Run `check_python.bat` to display the interpreters and project environments detected by Windows.

### Manual setup (PowerShell)

For Python 3.12 — full capstone:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install --upgrade pip
.\.venv312\Scripts\python.exe -m pip install -r requirements-py312.txt
.\.venv312\Scripts\python.exe -m uvicorn api.main:app --reload
```

For Python 3.14 — compatibility profile without CrewAI:

```powershell
py -3.14 -m venv .venv314
.\.venv314\Scripts\python.exe -m pip install --upgrade pip
.\.venv314\Scripts\python.exe -m pip install -r requirements-py314.txt
.\.venv314\Scripts\python.exe -m uvicorn api.main:app --reload
```

To configure PyCharm, open **Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Existing**, then select `.venv312\Scripts\python.exe` or `.venv314\Scripts\python.exe`. Do not select the global Python installation directly; use the project virtual environment.

The root `requirements.txt` is also version-marked: pip installs CrewAI only when the active interpreter is below Python 3.14. The explicit profile files are provided to make setup and troubleshooting easier.

## Browser UI (new)

The project now includes a responsive, browser-based support console. It is served by the same FastAPI application; no separate Node build, React install, or external frontend service is required. Start the server and open **http://127.0.0.1:8000/**. The interactive Swagger/OpenAPI page remains available at **http://127.0.0.1:8000/docs** for API testing.

UI sections:

- **Overview:** seeded order/category/status metrics, delayed-shipment rate, runtime component status, recent orders, and the agent workflow.
- **AI Assistant:** customer-support chat with policy suggestions, order-ID lookups, groundedness/source indicators, trace IDs, and request insights. A new conversation starts a fresh in-process session.
- **Order explorer:** searchable/filterable synthetic orders, order details, escalation score, threshold, and formula.
- **Knowledge base:** browse all authored policy documents and add a new text document through the API. Restart the service to re-index newly added documents.
- **Evaluation:** 15-query, four-metric scorecard, empirical retrieval threshold, and fixed-overlap vs sentence-chunk precision/recall comparison.
- **Governance:** medium-risk rationale, least-autonomy policy, token cap, cache details, framework execution evidence, and masked JSONL request logs.

The UI is plain HTML/CSS/JavaScript served from `web/`; all data comes from the local FastAPI application. New dashboard endpoints are under `/api/` and do not replace the capstone's core implementation.

Run API:

```bash
uvicorn api.main:app --reload
```

On Windows, run `setup.bat` once to create the selected environment, then use `start_app.bat` to launch the dashboard at http://127.0.0.1:8000/.

- `GET /health`
- `POST /ask` body: `{"query":"What is the return window for Beauty?","session_id":"demo"}`
- `POST /add-document` body: `{"doc_id":"13_new_policy","text":"At least twenty characters of synthetic policy text."}`
- `WS /ws/chat` JSON messages: `{"query":"...","session_id":"demo"}`. A client disconnect is caught as `WebSocketDisconnect`.
- `GET /api/dashboard`, `/api/orders`, `/api/orders/{record_id}`, `/api/knowledge`, `/api/evaluation`, `/api/rag-report`, `/api/demos`, and `/api/logs` provide dashboard read models.
- `POST /api/evaluation/run` regenerates the 15-query evaluation transcript.

## Repository map

`dataset/` generator and synthetic orders; `knowledge_base/` twelve authored policy documents; `rag/` loaders, both chunkers, embeddings, separate Chroma collections, calibrated retrieval; `agents/` CrewAI `BaseLLM`, three agents and tools; `memory/` session history and LangChain adapter; `guardrails/` PII/injection and groundedness checks; `review/` AutoGen RoundRobinGroupChat integration plus deterministic fallback; `governance/` budget and least-autonomy controls; `api/` FastAPI HTTP/WebSocket and dashboard API; `web/` responsive browser UI; `evaluation/` document-level retrieval metrics and 15-query rubric; `transcripts/` generated demonstrations. Run `python -m demos.crew_demo`, `python -m demos.memory_demo`, and `python -m demos.autogen_demo` to exercise the optional framework paths after installing dependencies. Run `python -m unittest discover -s tests -v` to execute the core tests and dashboard/API smoke tests.

## Measured retrieval and escalation results (seed-42 build environment)

The build-time calibration used the deterministic lexical fallback because SentenceTransformers was not installed in the packaging environment. The five in-scope top-1 similarities were `0.329, 0.151, 0.236, 0.178, 0.267`; the two out-of-scope similarities were `0.000, 0.000`; the measured midpoint threshold was `0.075378`. Re-run `python -m rag.calibrate` after the SentenceTransformer model is locally cached; do not reuse these fallback values for the SentenceTransformer backend.

The document-level evaluation recommends fixed-size-with-overlap on this dataset: precision/recall `0.305/0.917`, compared with sentence chunks `0.285/0.833`. The selected production collection is therefore `nykaa_fixed_overlap`.

The escalation score is `0.60 * delayed_shipment + 0.40 * (days_since_created / 30)`. In the seed-42 dataset, P80 of order age is 23 days; the threshold is `0.60 + 0.40*(23/30) = 0.907`, so escalation is recommended for composite scores strictly above 0.907.

## Task coverage map

| Task | Implementation |
|---|---|
| 1 dataset | `dataset/dataset.py` |
| 2 12+ KB docs | `knowledge_base/*.txt` |
| 3 fixed + sentence chunks, embeddings, two Chroma collections/upsert | `rag/chunking.py`, `rag/embeddings.py`, `rag/vector_store.py` |
| 4 grounded answers + measured threshold | `rag/calibrate.py`, `rag/retrieval.py` |
| 5 per-query document precision/recall | `evaluation/rag_evaluation.py` |
| 6 order lookup + composite escalation | `tools.py` |
| 7 three CrewAI agents + `.kickoff()` | `agents/crew.py`, `service.py` |
| 8 session memory + LangChain adapter | `memory/session_memory.py` |
| 9 Pydantic response schema | `schemas.py` |
| 10 PII, injection, groundedness guardrails | `guardrails/` |
| 11 two HTTP endpoints + WebSocket | `api/main.py` |
| 12 masked JSONL structured logging | `logging_utils.py` |
| 13 15-query, four-metric evaluation | `evaluation/scale_evaluation.py` |
| 14 AutoGen 2-agent round robin, max_turns=2, verdict schema | `review/autogen_review.py` |
| 15 least autonomy, medium risk, request budget | `governance/` |
| 16 normalized-query response cache | `service.py` |

## Known boundaries and honest verification notes

1. This is a learning capstone prototype, not a production Nykaa service. The KB policies are invented from the assignment topic list, and the dataset is synthetic.
2. The deterministic `MOCK_LLM` uses evidence selection and rule-based review/scoring, not semantic reasoning. The 15-query judge scores are transparent rule-based proxies, not human ratings or a genuine LLM-as-judge.
3. The similarity threshold must be calibrated on your runtime's actual embedding backend by `python -m rag.calibrate`; inspect `rag/threshold.json` and the recorded values before reporting it. Do not reuse a threshold measured with hashing fallback as a SentenceTransformer threshold.
4. For complete framework acceptance, install the pinned dependencies and verify that the CrewAI and AutoGen integration tests execute rather than skip. Framework APIs can change; if the installed versions differ, resolve integration failures and regenerate transcripts before submitting.
5. The browser UI smoke-tested successfully against the FastAPI test client in the packaging environment. The four optional integrations (CrewAI, AutoGen, ChromaDB and SentenceTransformers) were not installed in that environment, so the UI deliberately labels their status as optional/fallback rather than claiming successful live execution. Install the pinned requirements and rerun the optional integration tests before final capstone submission.
6. No public GitHub repository is created by this ZIP. Create one public repository, push this folder, then submit that single URL.

## Governance and privacy

Only fabricated data is used. Phone numbers and card-last-four patterns are masked before model input and before JSONL logging. Customer names and delivery addresses are not reliably masked in keyless mode and must remain synthetic. The system is classified **Medium risk**: customer-support assistance can mislead or inconvenience customers, but it does not make medical, hiring, credit, or other high-impact decisions. Human escalation is recommended for unresolved or high-risk cases.

## Publish the single required GitHub repository

Create one **public** empty GitHub repository named `nykaa-support-agent`, then from this folder run:

```bash
git init
git add .
git commit -m "Complete Nykaa CrewAI support agent capstone"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nykaa-support-agent.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Submit only the resulting public repository URL. Do not commit `.env`, virtual environments, local vector-store data, or request logs.
