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
        name = project.name,
        description = project.description,
        status = project.status,
        start_date = project.start_date,
        end_date = project.end_date,
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
    update_data = project_data.model_dump(
         exclude_unset= True
    )
    new_start_date = update_data.get("start_date", project.start_date)
    new_end_date = update_data.get("end_date", project.end_date)

    if new_end_date is not None and new_end_date < new_start_date:
         raise HTTPException(
              status_code=422,
              detail="La fecha de finalizacion no puede ser anterior a la fecha de inicio"
         )

    for field, value in update_data.items():
         setattr(project, field, value)

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