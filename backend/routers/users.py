from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db
from backend.models import User, Role
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.security import hash_password



router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserResponse, 
             status_code=201,
             responses={
                 404:{"description":"Rol no encontrado"},
                 409:{"description":"Usuario duplicado"}
                 }
             )
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
): 
    existing_employee = db.scalar(
        select(User).where(
            User.employee_number == user_data.employee_number
        )
    )
    if existing_employee:
        raise HTTPException(
            status_code=409,
            detail="El numero de empleado ya está registrado"
        )
    existing_identification = db.scalar(
        select(User).where(
            User.identification == user_data.identification
        )
    )

    if existing_identification:
        raise HTTPException(
            status_code=409,
            detail="La identificación ya está registrada"
        )
    existing_role = db.scalar(
        select(Role).where(
            Role.id == user_data.role_id
        )
    )
    if not existing_role:
        raise HTTPException(
            status_code=404,
            detail="El rol especificado no existe"
        )
    
    db_user = User(
        employee_number = user_data.employee_number,
        identification = user_data.identification,
        password_hash = hash_password(user_data.password),
        role_id = user_data.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
@router.get("/", response_model= list[UserResponse])
def list_users(
    db:Session = Depends(get_db)
):
    users = db.scalars(
        select(User)
    ).all()

    return users

@router.get(
        "/{user_id}", 
        response_model=UserResponse,
        responses= {
            404:{"description": "Usuario no encomtrado"}
        }

)
def get_user(
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
    return user

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        404:{"description":"Usuario no encontrado"},
        409:{"description":"Datos de usuario duplicados"}
    }
)
def update_user(
    user_id:int,
    user_data:UserUpdate,
    db:Session = Depends(get_db)
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
    update_data = user_data.model_dump(exclude_unset=True)

    if "employee_number" in update_data:
        existing_employee = db.scalar(
            select(User).where(
            User.employee_number == update_data["employee_number"],
            User.id != user_id
            )
        )

        if existing_employee:
            raise HTTPException(
                status_code=409,
                detail="El numero de empleado ya está registrado"
            )
    if "identification" in update_data:
        existing_identification = db.scalar(
            select(User).where(
                User.identification == update_data["identification"],
                User.id != user_id
            )
        )
        if existing_identification:
            raise HTTPException(
                status_code= 409,
                detail="La identificación ya está registrada"
            )
    if "role_id" in update_data:
        existing_role = db.scalar(
            select(Role).where(
                Role.id == update_data["role_id"]
            )
        )
        if not existing_role:
            raise HTTPException(
                status_code=404,
                detail="El rol especificado no existe"
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user