from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project
from backend.schemas.project import (
    ProjectUpdate,
    ProjectResponse,
    ProjectCreate
    )

router = APIRouter()

@router.get("/projects",
         response_model=list[ProjectResponse]
)
def get_projects(
    db:Session = Depends(get_db),
):
    statement = select(Project)
    projects = db.scalars(statement).all()

    return projects

@router.post(
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

@router.get("/projects/{project_id}",
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
@router.patch(
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


@router.delete(
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