# Login gateway for DB-GPT on Railway. DB-GPT has no login of its own, so this Caddy
# reverse proxy is the only public entry point. Official image, pinned by version and digest.
FROM caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0

COPY Caddyfile /etc/caddy/Caddyfile
COPY gateway-start.sh /gateway-start.sh
RUN chmod 755 /gateway-start.sh

EXPOSE 8080
CMD ["/gateway-start.sh"]
