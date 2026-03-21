from pydantic import BaseModel


class RetrainResponse(BaseModel):
    status: str
    message: str
    model_path: str
