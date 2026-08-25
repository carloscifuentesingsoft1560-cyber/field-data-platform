from fastapi import FastAPI
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


app = FastAPI()


@app.get("/")
def root():
    return {"message": "Field Data Platform API"}


@app.post("/projects")
def create_project(project: ProjectCreate):
    return project