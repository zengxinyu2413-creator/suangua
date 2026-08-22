"""
main.py
=======
中国术数平台 — FastAPI application entry point.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8888 --reload
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from api.bazi          import router as bazi_router
from api.liuyao        import router as liuyao_router
from api.qimen         import router as qimen_router
from api.fengshui      import router as fengshui_router
from api.date_selection import router as date_router
from api.knowledge     import router as knowledge_router
from api.agent         import router as agent_router
from api.models        import router as models_router
from api.ziwei         import router as ziwei_router
from api.narration     import router as narration_router
from api.auth          import router as auth_router

# ─────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="中国术数平台 API",
    description=(
        "中国传统命理系统后端 API\n\n"
        "涵盖：八字 | 六爻 | 奇门遁甲 | 风水 | 择日 | 知识库"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

# CORS — allow all origins so local dev always works regardless of how
# the .env was written (JSON array, comma-separated, or missing entirely).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────

app.include_router(bazi_router,       prefix="/api/v1")
app.include_router(liuyao_router,     prefix="/api/v1")
app.include_router(qimen_router,      prefix="/api/v1")
app.include_router(fengshui_router,   prefix="/api/v1")
app.include_router(date_router,       prefix="/api/v1")
app.include_router(knowledge_router,  prefix="/api/v1")
app.include_router(agent_router,      prefix="/api/v1")
app.include_router(models_router,     prefix="/api/v1")
app.include_router(ziwei_router,      prefix="/api/v1")
app.include_router(auth_router,       prefix="/api/v1")
app.include_router(narration_router,  prefix="/api/v1")

# ─────────────────────────────────────────────────────────────
# Frontend static hosting (production / cloud deployment)
#
# If the frontend has been built (frontend/dist exists), we serve
# it from the SAME process/port as the API — convenient for cloud
# platforms that only expose a single port. Run `npm run build`
# inside frontend/ before starting the server to enable this.
# In local dev (no dist/ folder) this is a no-op and "/" falls
# back to the JSON status response below.
# ─────────────────────────────────────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(_HERE, "frontend", "dist")
_has_frontend = os.path.isdir(FRONTEND_DIST) and os.path.isfile(os.path.join(FRONTEND_DIST, "index.html"))

if _has_frontend:
    _assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

# ─────────────────────────────────────────────────────────────
# Root + health check
# ─────────────────────────────────────────────────────────────

@app.get("/", tags=["系统"])
async def root():
    if _has_frontend:
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    return {
        "name":    "中国术数平台 API",
        "version": "2.0.0",
        "status":  "running",
        "docs":    "/docs",
        "modules": ["八字", "六爻", "奇门遁甲", "风水", "择日", "知识库", "AI命理顾问"],
    }


@app.get("/health", tags=["系统"])
async def health():
    # 优先反映云平台实际注入的运行端口（$PORT），没有则回退到 config 默认值，
    # 避免 /health 显示的端口和 uvicorn 实际监听端口不一致造成误导。
    runtime_port = int(os.environ.get("PORT", settings.app_port))
    return {
        "success": True,
        "data": {
            "status": "ok",
            "version": "2.1.0",
            "modules": ["bazi", "liuyao", "qimen", "fengshui", "date_selection", "knowledge"],
            "port": runtime_port,
            "frontend_hosted": _has_frontend,
        },
        "message": "运行正常",
    }


# ─────────────────────────────────────────────────────────────
# Global error handler
# ─────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": str(exc), "data": None},
    )


# ─────────────────────────────────────────────────────────────
# SPA fallback — MUST be the last route registered.
# Serves any unmatched GET path from the built frontend so that
# deep links / browser refreshes on client-side routes (e.g.
# /bazi, /qimen, /settings) work correctly instead of 404ing.
# API routes, /docs, /health etc. are matched above and take
# priority, so this only ever catches frontend page paths.
# ─────────────────────────────────────────────────────────────

if _has_frontend:
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
