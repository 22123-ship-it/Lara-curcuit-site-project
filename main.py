from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import bcrypt

app = FastAPI()

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="race123",
        database="racetrack_db"
    )

# 3. Data Models
class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# 1. Трябва да имаш модел за резервацията в началото на файла
class Reservation(BaseModel):
    user_id: int
    track_date: str
    category: str
    package: str

# 2. Ендпоинт за резервация (Увери се, че е точно така)
@app.post("/book")
def book_track(res: Reservation):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO reservations (user_id, track_date, category, package) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (res.user_id, res.track_date, res.category, res.package))
        conn.commit()
        return {"message": "Success"}
    except Exception as e:
        print(f"Грешка при запис: {e}") # Ще го видиш в терминала
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# 3. Ендпоинт за администратора
@app.get("/admin/reservations")
def get_all_reservations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT r.id, u.full_name, u.email, r.track_date, r.category, r.package 
            FROM reservations r 
            JOIN users u ON r.user_id = u.id
            ORDER BY r.track_date DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (user.email,))
        db_user = cursor.fetchone()
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Грешен имейл или парола.")

        # Check password using bcrypt
        password_byte_enc = user.password.encode('utf-8')
        hashed_db_password = db_user['password_hash'].encode('utf-8')
        
        if not bcrypt.checkpw(password_byte_enc, hashed_db_password):
            raise HTTPException(status_code=401, detail="Грешен имейл или парола.")
        
        return {
            "user_id": db_user['id'], 
            "full_name": db_user['full_name'],
            "email": db_user['email']
        }
    except Exception as e:
        print(f"Login Error: {e}")
        raise HTTPException(status_code=500, detail="Вътрешна системна грешка.")
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # <-- Добавено dictionary=True
    try:
        query = "SELECT id, email, password_hash FROM users WHERE email = %s"
        cursor.execute(query, (user.email,))
        db_user = cursor.fetchone()
        
        if db_user and bcrypt.checkpw(user.password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
            # Връщаме ID и Email, за да ги ползваме във Frontend-а
            return {
                "message": "Success", 
                "user_id": db_user['id'], 
                "email": db_user['email']
            }
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    finally:
        cursor.close()
        conn.close()

@app.get("/my-reservations")
def get_user_reservations(email: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT r.id, r.track_date, r.category, r.package 
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = %s
            ORDER BY r.track_date DESC
        """
        cursor.execute(query, (email,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.delete("/admin/reservations/{res_id}")
def delete_reservation(res_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM reservations WHERE id = %s"
    cursor.execute(query, (res_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Deleted"}

    # --- USER PROFILE ROUTE ---
@app.get("/my-reservations/{user_id}")
def get_user_reservations(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # We look for reservations specifically for THIS user
        query = "SELECT id, track_date, category, package FROM reservations WHERE user_id = %s ORDER BY track_date DESC"
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()
        return data
    finally:
        cursor.close()
        conn.close()