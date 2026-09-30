"""HTTP entry point: the MCP endpoint at /mcp, the voice simulator at /voice, and a health check."""

from __future__ import annotations

import argparse
import contextlib
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .config import settings
from .mcp_server import build_server
from .seed import seed
from .service import CareService
from .store import make_store
from .voice import VoiceSessions
from .web import voice_routes

log = logging.getLogger("carecircle")


def create_app(service: CareService | None = None, voice: VoiceSessions | None = None) -> Starlette:
    if service is None:
        store = make_store()
        if not store.get("profile", "main"):
            log.info("Empty store: seeding demo household")
            seed(store)
        service = CareService(store)

    mcp = build_server(service)
    mcp_app = mcp.streamable_http_app()
    voice = voice or VoiceSessions()

    async def health(_):
        return JSONResponse({"ok": True, "protocol": "2025-11-25", "store": settings.store, "llm": settings.llm_provider})

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        async with mcp.session_manager.run():
            try:
                yield
            finally:
                await voice.close_all()

    routes = [Route("/health", health), *voice_routes(voice), Mount("/", app=mcp_app)]
    app = Starlette(routes=routes, lifespan=lifespan)
    app.state.service = service
    app.state.mcp = mcp
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="CareCircle MCP server")
    parser.add_argument("--seed", action="store_true", help="reset the store to the demo household and exit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.seed:
        seed(make_store())
        print("Seeded demo household.")
        return
    log.info("Voice simulator: http://127.0.0.1:%s/voice", settings.port)
    uvicorn.run(create_app(), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
