
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

# --- Configuration ---
# Clé secrète pour signer les jetons JWT. En production, utilisez une clé plus complexe et stockez-la de manière sécurisée.
SECRET_KEY = "votre_super_cle_secrete_a_changer" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Contexte de hachage de mot de passe ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Schéma OAuth2 ---
# Indique à FastAPI où trouver le jeton (dans la requête entrante)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Fonctions Utilitaires ---

def verify_password(plain_password, hashed_password):
    """Vérifie si un mot de passe en clair correspond à un mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Génère le hachage d'un mot de passe."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crée un nouveau jeton d'accès JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dépendance FastAPI pour obtenir l'utilisateur actuel à partir d'un jeton.
    C'est la fonction qui protège les endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Ici, vous pourriez charger l'utilisateur depuis la base de données si nécessaire
        # Pour cet exemple, nous retournons simplement le nom d'utilisateur.
        return {"username": username}
    except JWTError:
        raise credentials_exception
