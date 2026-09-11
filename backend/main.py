from fastapi import FastAPI

from backend.routers.projects import router as projects_router
from backend.routers.users import router as users_router
from backend.routers.user_projects import router as user_projects_router
from backend.routers.forms import router as forms_router
from backend.routers.form_versions import router as form_versions_router
from backend.routers import form_fields, field_options

app = FastAPI()

app.include_router(projects_router)
app.include_router(users_router)
app.include_router(user_projects_router)
app.include_router(forms_router)
app.include_router(form_versions_router)
app.include_router(form_fields.router)
app.include_router(field_options.router)


@app.get("/")
def root():
    return {"message": "Field Data Platform API"}


