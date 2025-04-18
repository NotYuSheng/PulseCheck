import json
import os
from typing import Dict
from models import Service
import requests

DATA_FILE = os.path.join(os.environ.get("DATA_DIR", "."), "services.json")

def _load_services() -> Dict[str, dict]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_services():
    with open(DATA_FILE, "w") as f:
        json.dump(services, f, indent=2)

# Persistent service registry
services: Dict[str, dict] = _load_services()

def register_service(service: Service):
    services[service.name] = {
        "description": service.description,
        "healthcheck_url": str(service.healthcheck_url),
        "status": "unknown"
    }
    _save_services()

def get_services():
    return services

def remove_service(name: str):
    if name in services:
        del services[name]
        _save_services()

def ping_services():
    for name, info in services.items():
        url = info.get("healthcheck_url")
        if not url:
            services[name]["status"] = "not checked"
            continue
        try:
            response = requests.get(url, timeout=2)
            services[name]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            services[name]["status"] = "unreachable"
    _save_services()
