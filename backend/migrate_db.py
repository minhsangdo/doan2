import sqlite3

def upgrade():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    # Try to add email column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
        print("Added 'email' column.")
    except sqlite3.OperationalError as e:
        print("Column 'email' may already exist:", e)
        
    # Try to add reset_token column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR")
        print("Added 'reset_token' column.")
    except sqlite3.OperationalError as e:
        print("Column 'reset_token' may already exist:", e)
        
    # Try to add reset_token_expire column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expire DATETIME")
        print("Added 'reset_token_expire' column.")
    except sqlite3.OperationalError as e:
        print("Column 'reset_token_expire' may already exist:", e)

    # Try to add khoi_thi column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN khoi_thi VARCHAR")
        print("Added 'khoi_thi' column.")
    except sqlite3.OperationalError as e:
        print("Column 'khoi_thi' may already exist:", e)

    # Try to add diem_du_kien column
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN diem_du_kien FLOAT")
        print("Added 'diem_du_kien' column.")
    except sqlite3.OperationalError as e:
        print("Column 'diem_du_kien' may already exist:", e)

    # Bảng mới: Ngành quan tâm & Phản hồi câu trả lời
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_favorite_majors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            ma_nganh VARCHAR NOT NULL,
            ten_nganh VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ma_nganh)
        )
    """)
    print("Table 'user_favorite_majors' ready.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL REFERENCES chat_messages(id),
            user_id INTEGER REFERENCES users(id),
            rating VARCHAR NOT NULL,
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Table 'message_feedbacks' ready.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    upgrade()
