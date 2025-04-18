from pydantic import BaseModel, HttpUrl

class Service(BaseModel):
    name: str
    description: str
    healthcheck_url: HttpUrl
