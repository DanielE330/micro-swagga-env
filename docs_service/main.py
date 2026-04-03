import os
import json
import copy
import time
import asyncio

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

CACHE_TTL = int(os.getenv("CACHE_TTL", "30"))

_cache_time: float = 0
_services: list[dict] = []  # [{host, port, prefix, title, spec}]


def _parse_env() -> list[dict]:
    raw = os.getenv("SERVICES", "")
    result = []
    for entry in raw.split(","):
        entry = entry.strip()
        if "=" not in entry or ":" not in entry:
            continue
        addr, rest = entry.rsplit("=", 1)
        host, port = addr.rsplit(":", 1)
        if "|" in rest:
            prefix, openapi_path = rest.split("|", 1)
        else:
            prefix = rest
            openapi_path = "/openapi.json"
        result.append({
            "host": host.strip(),
            "port": int(port),
            "prefix": prefix.strip(),
            "openapi_path": openapi_path.strip(),
        })
    return result


async def _discover():
    global _cache_time, _services
    if time.time() - _cache_time < CACHE_TTL and _services:
        return

    entries = _parse_env()
    results = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        async def fetch(svc):
            try:
                url = f"http://{svc['host']}:{svc['port']}{svc['openapi_path']}"
                r = await client.get(url)
                if r.status_code == 200:
                    spec = r.json()
                    svc["spec"] = spec
                    svc["title"] = spec.get("info", {}).get("title", svc["host"])
                    return svc
            except Exception:
                pass
            return None

        results = await asyncio.gather(*[fetch(s) for s in entries])

    _services = [s for s in results if s]
    _cache_time = time.time()


@app.get("/specs/{host}")
async def get_spec(host: str):
    await _discover()
    for svc in _services:
        if svc["host"] == host:
            spec = copy.deepcopy(svc["spec"])
            spec["servers"] = [{"url": svc["prefix"]}]
            return JSONResponse(spec)
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/", response_class=HTMLResponse)
async def docs():
    await _discover()
    urls = [{"url": f"/docs/specs/{s['host']}", "name": s["title"]} for s in _services]
    primary = urls[0]["name"] if urls else ""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <title>API Docs</title>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
    SwaggerUIBundle({{
        urls: {json.dumps(urls)},
        "urls.primaryName": {json.dumps(primary)},
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        layout: "StandaloneLayout",
    }})
    </script>
</body>
</html>"""
