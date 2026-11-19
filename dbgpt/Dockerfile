# DB-GPT webserver for Railway. Official image, pinned by version and digest.
FROM eosphorosai/dbgpt-openai:v0.8.3@sha256:89ec4eb23f2863888d7f92896342c64bdd849a679a8a129eee5a6b2b309b8776

# All state goes to the Railway volume mounted at /data (see railway-start.sh).

COPY dbgpt-railway.toml /app/configs/dbgpt-railway.toml
COPY railway_db_init.py /railway/railway_db_init.py
COPY railway-start.sh /railway/railway-start.sh
RUN chmod 755 /railway/railway-start.sh

WORKDIR /app
EXPOSE 5670
CMD ["/railway/railway-start.sh"]
