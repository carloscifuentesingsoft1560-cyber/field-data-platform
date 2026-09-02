from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import UserProject, User, Project
from backend.schemas.user_project import (
    UserProjectCreate,
    UserProjectResponse,
)

router = APIRouter(
    prefix="/user-projects",
    tags=["user-projects"]
)

@router.post(
    "/",
    response_model=UserProjectResponse,
    status_code=201,
    responses={
        404:{"description": "Usuario o proyecto no encontrado"},
        409:{"description": "El ususario ya está asignado al proyecto"}
    }
)
def create_user_project(
    assignment: UserProjectCreate,
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(
            User.id == assignment.user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    project = db.scalar(
        select(Project).where(
            Project.id == assignment.project_id
        )
    )
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    existing_assignment = db.scalar(
        select(UserProject).where(
            UserProject.user_id == assignment.user_id,
            UserProject.project_id == assignment.project_id
        )
    )
    if existing_assignment:
        raise HTTPException(
            status_code=409,
            detail="El usuario ya está asignado a este proyecto"
        )

    db_assignment = UserProject(
        user_id = assignment.user_id,
        project_id = assignment.project_id
    )

    db.add(db_assignment)

    db.commit()
    db.refresh(db_assignment)

    return db_assignment

@router.get(
    "/user/{user_id}",
    response_model=list[UserProjectResponse],
    responses= {
        404:{"description":"Usuario no encontrado"}
    }
)
def get_project_by_user(
    user_id:int,
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )
    if not user:
        raise HTTPException(
            status_code= 404,
            detail="Usuario no encontrado"
        )
    assignments = db.scalars(
        select(UserProject).where(
        UserProject.user_id == user_id
        )
    ).all()

    return assignments
@router.get(
    "/project/{project_id}",
    response_model=list[UserProjectResponse],
    responses={
         404:{"description":"Proyecto no encontrado"}
        }
)

def get_users_by_project(
    project_id:int,
    db: Session = Depends(get_db)
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id
        )
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail= "Proyecto no encontrado"
        )


    assignments = db.scalars(
        select(UserProject).where(
            UserProject.project_id == project_id
        )
    ).all()

    return assignments

@router.delete(
    "/{user_id}/{project_id}",
    status_code=204,
    responses={
        404:{"description":"Asignación no encontrada"}
    }
)
def delete_user_project(
    user_id: int,
    project_id: int,
    db: Session = Depends(get_db)
):
    assignment = db.scalar(
        select(UserProject).where(
        UserProject.user_id == user_id,
        UserProject.project_id == project_id
       )
    )

    if not assignment:
        raise HTTPException(
            status_code= 404,
            detail="Asignación no encontrada"
        )
    db.delete(assignment)
    db.commit()