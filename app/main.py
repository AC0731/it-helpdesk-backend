from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import diagnostics, tickets

app = FastAPI(
    title="IT Helpdesk Diagnostic API",
    description="Backend service for automated network diagnostics.",
    version="1.1.0" # Version bump to show progress!
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://it-support-portal.vercel.app"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect our modular routers
app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])

@app.get("/")
async def root():
    return {"status": "online", "message": "IT Helpdesk API is running modularly."}