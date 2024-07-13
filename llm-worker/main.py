from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import make_context

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ctx = make_context()

@app.post("/api/chat")
def chat(req: Dict[str, Any]):
    message = req["message"]
    project_id = int(req["project_id"])

    ctx.logger.info(f"request: {message}")
    with ctx.db_pool() as session:
        resp = ctx.deps.llm.send_message(session, project_id, message)
        ctx.logger.info(f"response: {resp}")

        if "msg" in resp:
            return {"message": resp["msg"]}
        else:
            return {"message": "Request failed"}
