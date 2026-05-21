from fastapi import FastAPI
from app.tools import store_memory, search_memory

app = FastAPI(title="MCP Personal Memory Server")

@app.get("/")
def home():
    return {"message": "MCP Memory Server is running"}

@app.post("/store")
def store(text: str):
    return store_memory(text)

@app.get("/search")
def search(query: str):
    return search_memory(query)