from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import database

# ==============================================================================
# CONFIGURATION DE LA SÉCURITÉ
# ==============================================================================

# Clé secrète pour signer les jetons JWT. À remplacer par une clé forte en production.
SECRET_KEY = "votre_super_cle_secrete_a_remplacer_en_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexte pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma OAuth2 pour que FastAPI sache comment trouver le jeton
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ==============================================================================
# FONCTIONS DE GESTION DES MOTS DE PASSE
# ==============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en clair contre sa version hachée."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hache un mot de passe pour le stockage."""
    return pwd_context.hash(password)

# ==============================================================================
# FONCTIONS DE GESTION DES JETONS JWT
# ==============================================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crée un nouveau jeton d'accès JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==============================================================================
# DÉPENDANCE POUR OBTENIR L'UTILISATEUR ACTUEL
# ==============================================================================

def get_current_user(token: str = Depends(oauth2_scheme), db: database.Session = Depends(database.get_db)) -> database.User:
    """
    Décode le jeton JWT pour obtenir l'utilisateur actuel.
    C'est la dépendance qui protège les routes de l'API.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        user = database.get_user_by_username(db, username=username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception