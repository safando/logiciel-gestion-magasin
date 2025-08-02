
import database
import auth
from sqlalchemy.orm import Session

def reset_admin_password():
    """
    Réinitialise le mot de passe de l'utilisateur admin.
    Supprime l'ancien utilisateur s'il existe et en crée un nouveau
    avec un mot de passe correctement haché.
    """
    # S'assurer que les tables existent
    database.create_tables()

    db: Session = next(database.get_db())
    
    # Définir le nom d'utilisateur et le mot de passe
    username = "admin"
    password = "Dakar2026@"

    # 1. Supprimer l'utilisateur existant
    user = database.get_user_by_username(db, username=username)
    if user:
        print(f"Utilisateur '{username}' trouvé. Suppression...")
        db.delete(user)
        db.commit()
        print(f"Utilisateur '{username}' supprimé.")
    else:
        print(f"L'utilisateur '{username}' n'existait pas, création en cours.")

    # 2. Créer le nouvel utilisateur avec le mot de passe correctement haché
    hashed_password = auth.get_password_hash(password)
    new_user = database.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    
    print(f"L'utilisateur '{username}' a été créé avec succès avec le nouveau mot de passe.")
    
    db.close()

if __name__ == "__main__":
    reset_admin_password()
