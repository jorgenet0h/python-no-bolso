from fastapi import FastAPI

app = FastAPI(title="Python no Bolso API")


@app.get("/health")
def health() -> dict[str, str]:
    # Banco entra no PR 5; por ora só confirma que a API está de pé.
    return {"status": "ok"}
