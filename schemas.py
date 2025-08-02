
from pydantic import BaseModel
from datetime import datetime

class ProduitBase(BaseModel):
    nom: str
    prix_achat: float
    prix_vente: float
    quantite: int

class ProduitCreate(ProduitBase):
    pass

class Produit(ProduitBase):
    id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str

    class Config:
        orm_mode = True
