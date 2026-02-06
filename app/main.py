import os
import sys
from pathlib import Path

# 스크립트 직접 실행 시(__package__ 미설정) 상위 폴더를 모듈 탐색 경로에 추가
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

# .env를 가능하면 자동 로드하되, 없거나 python-dotenv 미설치면 조용히 패스
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"   # sejong-auth-svc/.env
def _load_env() -> bool:
    if not ENV_PATH.exists():
        return False
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return False
    load_dotenv(ENV_PATH)
    return True

ENV_LOADED = _load_env()
DEFAULT_PORT = int(os.getenv("PORT", "8081"))
APP_VERSION = "1.0.0"

from fastapi import FastAPI
from app.auth_router import router as auth_router

app = FastAPI(title="Sejong Auth Service", version=APP_VERSION)
app.include_router(auth_router)

@app.get("/healthz")
def health():
    # 로딩된 환경 상태를 노출(민감 정보는 포함하지 않음)
    return {
        "ok": True,
        "version": APP_VERSION,
        "env_loaded": ENV_LOADED,
        "port": DEFAULT_PORT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=DEFAULT_PORT,
        reload=True,
    )
