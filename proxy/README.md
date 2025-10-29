# Proxy service (nginx)

This folder provides a minimal nginx-based reverse proxy used by `docker-compose.yml`.

Behavior:
Behavior in production (this repo):
- Requests starting with `/sports/api/` are proxied to the `api` service on port `8000`.
- Requests to `/sports/ws/` are proxied to `api` with websocket upgrade headers.
- The UI is served under the `/sports/` base path and proxied to the `ui` service on port `3000`.

How to build/use:

From the repository root:

```bash
docker-compose up --build proxy
```

Notes:
- The nginx config assumes the services are reachable by the Docker Compose service names `api` and `ui`.
- If your UI is served under a subpath (e.g. `/quranic/`), you may need to adjust the UI build or nginx config.
