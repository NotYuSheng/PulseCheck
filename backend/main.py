from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models import Service
from registry import register_service, get_services, ping_services
import yaml

app = FastAPI(title="Pulse Check – Service Registry")

@app.post("/register")
async def register(service: Service):
    register_service(service)
    return {"message": f"Service '{service.name}' registered."}

@app.get("/services")
async def list_services():
    return get_services()

@app.get("/ping")
async def ping():
    ping_services()
    return {"message": "Pinged all services and updated status."}

@app.delete("/services/{name}")
async def delete_service(name: str):
    from registry import services, remove_service # Import the services dict

    if name not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    remove_service(name)
    return {"message": f"Service '{name}' removed."}
    return {"message": f"Service '{name}' removed."}