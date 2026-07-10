from app import create_app
from extensions import db
from models.user import User


DEFAULT_USERS = [
    {
        "nama_lengkap": "Administrator",
        "username": "admin",
        "email": "admin@se2026.local",
        "password": "admin123",
        "role": "admin",
    },
    {
        "nama_lengkap": "Pengguna Monitoring",
        "username": "user",
        "email": "user@se2026.local",
        "password": "user123",
        "role": "user",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        try:
            for item in DEFAULT_USERS:
                existing = User.query.filter(
                    (User.username == item["username"]) | (User.email == item["email"])
                ).first()
                if existing:
                    print(f"Akun {item['username']} sudah ada, dilewati.")
                    continue
                user = User(
                    nama_lengkap=item["nama_lengkap"],
                    username=item["username"],
                    email=item["email"],
                    role=item["role"],
                    is_active=True,
                )
                user.set_password(item["password"])
                db.session.add(user)
                print(f"Akun {item['username']} dibuat.")
            db.session.commit()
            print("Seed pengguna selesai.")
        except Exception as exc:
            db.session.rollback()
            raise SystemExit(f"Gagal membuat akun: {exc}") from exc


if __name__ == "__main__":
    seed()

