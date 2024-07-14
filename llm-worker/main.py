from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .chat_db import add_project, del_project, get_project_list
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

@app.get("/api/chat/history")
def history(project_id: int):
    out_msgs = []
    with ctx.db_pool() as session:
        (history, _metadata) = ctx.deps.conversation_history.get_data(session, project_id)
        for msg in history:
            if type(msg["content"]) != str:
                continue
            out_msgs.append({
                "isUser": msg["role"] == "user",
                "content": msg["content"],
            })
    return out_msgs

@app.get("/api/chat/projects")
def projects():
    out_projects = []
    with ctx.db_pool() as session:
        projects = get_project_list(session)
        for p in projects:
            out_projects.append({"id": p.id, "name": p.name})
    return out_projects

@app.post("/api/chat/projects")
def add_new_project(req: Dict[str, str]):
    name = req["name"]
    with ctx.db_pool() as session:
        project = add_project(session, name)
        return {"id": project.id, "name": project.name}

@app.delete("/api/chat/history")
def delete_project(project_id: int):
    with ctx.db_pool() as session:
        del_project(session, project_id)

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
