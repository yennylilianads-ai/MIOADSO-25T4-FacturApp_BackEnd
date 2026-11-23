from src.app import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("UPDATE users SET role='ADMIN' WHERE id=1"))
    conn.commit()
    result = conn.execute(text("SELECT id, email, role FROM users WHERE id=1"))
    print(list(result))
    print("LISTO! Ya eres ADMIN")