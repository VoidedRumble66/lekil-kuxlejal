from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.evolution_stream import router as evolution_router

app = FastAPI(title="Motor Genético SSE", version="1.0.0")

# CORS middleware for Vercel domains and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.vercel.app", "https://kinich-agro.vercel.app", "https://itzamna.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

app.include_router(evolution_router, prefix="/api")
