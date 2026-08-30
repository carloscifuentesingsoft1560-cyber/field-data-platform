from fastapi import FastAPI

from backend.routers.projects import router as projects_router

from backend.routers.users import router as users_router


app = FastAPI()

app.include_router(projects_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "Field Data Platform API"}


