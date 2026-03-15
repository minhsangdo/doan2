from core.database import SessionLocal
from models.database_models import User
from core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()

    if not admin_user:
        # Default password will be "admin123"
        hashed_password = get_password_hash("admin123")
        new_user = User(username="admin", email="admin@dnc.edu.vn", hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        print("Đã tạo tài khoản admin thành công!\\n- Tài khoản: admin\\n- Mật khẩu: admin123")
    else:
        print("Tài khoản admin đã tồn tại sẵn trong hệ thống.")
    db.close()

if __name__ == "__main__":
    create_admin()
