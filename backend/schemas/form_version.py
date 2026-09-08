from datetime import datetime

from pydantic import BaseModel

class FormVersionCreate(BaseModel):

    form_id: int
   
class FormVersionResponse(BaseModel):
    id: int
    form_id: int
    version_number: int
    status: str
    created_at: datetime

    model_config ={
        "from_attributes":True
    }
