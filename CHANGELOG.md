# Changelog

Breaking changes are listed first in each entry.

## 0.8.3-1 (2026-11-19)

First release of the Railway template.

* DB-GPT 0.8.3 (`eosphorosai/dbgpt-openai:v0.8.3`, pinned by digest).
* Railway MySQL for metadata. The start script waits for MySQL, creates the `dbgpt` database, loads upstream's schema plus the tables its SQL file misses, and applies upstream's upgrade scripts on later versions.
* Caddy 2.11.9 login gateway (generated password, cross-site request guard) as the only public service.
* Vectors, uploads, chart images, agent workspace and user skills on the DB-GPT volume at `/data`.
