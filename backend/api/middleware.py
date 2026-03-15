"""
CORS Middleware and basic logging for FastAPI
"""
import time
import logging
from fastapi import Request
from starlette.middleware.cors import CORSMiddleware
import os

logger = logging.getLogger("fastapi")

def setup_middlewares(app):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_url, "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        url = request.url.path
        if not url.startswith("/api/health"):
            logger.info(f"{request.method} {url} - {response.status_code} - {process_time*1000:.2f}ms")
            
        return response
