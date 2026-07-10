from sqlalchemy import or_

from models.user import User


def authenticate(identity: str, password: str):
    user = User.query.filter(
        or_(User.username == identity.strip(), User.email == identity.strip().lower())
    ).first()
    if not user or not user.is_active or not user.check_password(password):
        return None
    return user

