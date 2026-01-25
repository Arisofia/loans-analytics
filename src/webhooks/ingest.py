from fastapi import FastAPI, Request

app = FastAPI(title="Abaco Webhook Ingest")


@app.post("/ingest")
async def ingest(request: Request) -> dict[str, str]:
    payload = await request.json()
    if not payload:
        return {"status": "empty"}
    return {"status": "ok"}
