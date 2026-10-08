from pydantic import BaseModel


class DocumentOut(BaseModel):
    id_documents: int
    desc_tipo: str
    desc_documents: str

    class Config:
        from_attributes = True
