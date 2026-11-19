[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/db-gpt?utm_medium=integration&utm_source=button&utm_campaign=db-gpt)

# Deploy and Host DB-GPT on Railway

DB-GPT is an open-source (MIT) AI data assistant from the eosphoros-ai project. You ask questions about your databases, spreadsheets and documents in plain language and get SQL, charts, reports and answers back. It also has knowledge bases for retrieval-augmented answers, data agents and AWEL workflows. It runs against any OpenAI-compatible model API, with no GPU.

## About Hosting DB-GPT

This template runs DB-GPT 0.8.3 as three services on Railway's private network. Upstream's Docker setup pairs the webserver with MySQL but leaves the schema as a manual step, and DB-GPT has no login of its own. Here the start script creates and upgrades the MySQL schema on every boot, a Caddy gateway puts a generated username and password in front of the app, and every piece of state sits on a volume or in MySQL. The only thing you supply is an OpenAI-compatible API key. Each app service builds from a public GitHub repo pinned to an official image digest, so version bumps reach you as Railway update notices.

## Common Use Cases

* Chat with your database: connect MySQL, PostgreSQL, ClickHouse, DuckDB, SQLite and others, and ask questions in natural language (Text2SQL)
* Analyse Excel and CSV files and generate charts, dashboards and reports with data agents
* Build knowledge bases from documents and URLs for retrieval-augmented Q&A

## Dependencies for DB-GPT Hosting

* An OpenAI-compatible API key (OpenAI by default; OpenRouter, DeepSeek, SiliconFlow, a LiteLLM proxy and others work by changing the base URL and model names)
* MySQL for DB-GPT's metadata (included), and a volume for vectors and files (included)

### Deployment Dependencies

* [DB-GPT on GitHub](https://github.com/eosphoros-ai/DB-GPT) and its [v0.8.3 release](https://github.com/eosphoros-ai/DB-GPT/releases/tag/v0.8.3)
* [DB-GPT Docker deployment docs](https://docs.dbgpt.cn/docs/installation/docker)
* [Official image `eosphorosai/dbgpt-openai`](https://hub.docker.com/r/eosphorosai/dbgpt-openai)
* [Template source: aalfath/db-gpt-railway-template](https://github.com/aalfath/db-gpt-railway-template)

### Implementation Details

| Service | What it does | Public | Storage |
|---|---|---|---|
| **Gateway** | Caddy reverse proxy with basic auth and a cross-site request guard; the only public entry point | yes | none |
| **DB-GPT** | DB-GPT 0.8.3 webserver (`eosphorosai/dbgpt-openai:v0.8.3`, pinned by digest), on the private network only | no | volume at `/data`: Chroma vectors, uploads, chart images, agent workspace, your skills |
| **MySQL** | Railway's MySQL: chats, apps, knowledge spaces, data sources, flows | no | volume at `/var/lib/mysql` |

Start order: MySQL first; the DB-GPT start script waits for it (up to 5 minutes), creates the `dbgpt` database, loads upstream's schema (and adds the tables upstream's SQL file misses), then starts the webserver. On later boots it applies upstream's `upgrade_to_*.sql` files for any newer version. The Gateway shows "DB-GPT is starting up" until the app answers. The first boot takes 1–2 minutes.

**After deploy**

1. Open the **Gateway** service's public URL.
2. Log in with `GATEWAY_USERNAME` (default `admin`) and `GATEWAY_PASSWORD` (generated), both on the Gateway's Variables tab.
3. Try Chat Data against the preloaded `Walmart_Sales` example database, then add your own data sources and knowledge bases.

**Variables you may change** (on the DB-GPT service): `OPENAI_API_KEY` (asked at deploy), `OPENAI_API_BASE` and `LLM_MODEL_NAME` for another provider or model, `EMBEDDING_MODEL_NAME` and `EMBEDDING_MODEL_API_URL` (the full embeddings URL), and the optional `EMBEDDING_MODEL_API_KEY` when embeddings use a different key. `DBGPT_ENCRYPT_KEY` is generated once and encrypts stored credentials: don't change it later.

**Notes**

* Single tenant: anyone with the gateway password has full admin access, including SQL against connected databases.
* A custom domain goes on the Gateway; add it to `DBGPT_CORS_ALLOWED_ORIGINS` on the DB-GPT service too.
* DB-GPT uses about 1.5 GB of RAM: use the Hobby plan or higher.
* Updates: when this template's repo moves to a new DB-GPT release, Railway shows an update notice on your project. Read `CHANGELOG.md` first; the schema upgrade runs on the next boot. Back up the MySQL volume before major upgrades.

## Why Deploy DB-GPT on Railway?

<!-- Recommended: Keep this section as shown below -->
Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying DB-GPT on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
<!-- End recommended section -->

---

## Repository layout

* `dbgpt/`: `Dockerfile` (`FROM eosphorosai/dbgpt-openai:v0.8.3@sha256:89ec4eb23f2863888d7f92896342c64bdd849a679a8a129eee5a6b2b309b8776`), `dbgpt-railway.toml` (config read from variables), `railway-start.sh` (moves state onto the volume), `railway_db_init.py` (MySQL schema create and upgrade).
* `gateway/`: `Dockerfile` (`FROM caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0`), `Caddyfile`, `gateway-start.sh`.

Each Railway service builds from its folder (root directory `/dbgpt` or `/gateway`) on the `main` branch. A merge to `main` notifies everyone who deployed the template; they choose when to apply it.
