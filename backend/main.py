from fastapi import FastAPI

from backend.routers.projects import router as projects_router


app = FastAPI()

app.include_router(projects_router)


@app.get("/")
def root():
    return {"message": "Field Data Platform API"}


