from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project



class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: int
    name: str

class ProjectUpdate(BaseModel):
    name: str

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Field Data Platform API"}


@app.post(
        "/projects", 
        status_code=201,
        response_model=ProjectResponse,
)
def create_project(project: ProjectCreate,
    db: Session = Depends(get_db),):

    db_project = Project(
        name = project.name
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project

@app.get("/projects",
         response_model=list[ProjectResponse]
)
def get_projects(
    db:Session = Depends(get_db),
):
    statement = select(Project)
    projects = db.scalars(statement).all()

    return projects

@app.get("/projects/{project_id}",
         response_model=ProjectResponse,
         responses={404:{"description":"Project not found"}
        },  
)
def get_project(
    project_id: int,
    db:Session = Depends(get_db),
):
    statement = select(Project).where(
        Project.id == project_id
    )
    project = db.scalar(statement)

    if project is None:
        raise HTTPException(
            status_code= 404,
            detail= "Project not found",
        )
    
    return project

@app.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    responses={
        404: {"description":"Project not found"}
    },
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    statement = select(Project).where(
        Project.id == project_id
    )

    project = db.scalar(statement)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    project.name = project_data.name

    db.commit()
    db.refresh(project)


    return project

@app.delete(
    "/projects/{project_id}",
    responses= {
        404:{"description":"Project not found"}
    },
)
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db)
):
    statement = select(Project).where(
        Project.id == project_id
    )

    project = db.scalar(statement)
    if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found",
            )
    db.delete(project)
    db.commit()

    return {"menssage": "Project deleted"}