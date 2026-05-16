"""Run FastAPI vision service: run from huggingface-space root."""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "vision_api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        workers=1,
        reload=False,
    )
