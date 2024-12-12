from app.database import get_db
from app.auth.utils import hash_password, generate_tokens
import logging

class User:
    @staticmethod
    def create_user(email: str, password: str, name: str, phone: str = None, birth_date: str = None):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                return None, "Email already registered"

            hashed_pw = hash_password(password)

            cursor.execute(
                """
                INSERT INTO users(email, password_hash, name, phone, birth_date, status, created_at) 
                VALUES (%s, %s, %s, %s, %s, 'active', NOW())
                """,
                (email, hashed_pw, name, phone, birth_date)
            )
            db.commit()
            user_id = cursor.lastrowid

            if not user_id:
                return None, "Failed to create user"

            tokens = generate_tokens(user_id)

            return {
                "user_id": user_id,
                "email": email,
                "name": name,
                "access_token": tokens['access_token'],
                "token_type": "bearer"
            }, None

        except Exception as e:
            db.rollback()
            logging.error(f"User creation error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def authenticate(username: str, password: str):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT user_id, password_hash, status FROM users WHERE email=%s",
                (username,)
            )
            user = cursor.fetchone()

            if not user or user['status'] != 'active':
                return None, "Invalid credentials"

            if not verify_password(password, user['password_hash']):
                return None, "Invalid credentials"

            tokens = generate_tokens(user['user_id'])

            cursor.execute(
                "UPDATE users SET last_login=NOW() WHERE user_id=%s",
                (user['user_id'],)
            )
            db.commit()

            return {
                "access_token": tokens['access_token'],
                "token_type": "bearer"
            }, None

        except Exception as e:
            db.rollback()
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def update_profile(user_id: int, updates: dict):
        db = get_db()
        cursor = db.cursor()

        try:
            if 'current_password' in updates and 'new_password' in updates:
                cursor.execute(
                    "SELECT password_hash FROM users WHERE user_id = %s",
                    (user_id,)
                )
                current_hash = cursor.fetchone()[0]

                if not verify_password(updates['current_password'], current_hash):
                    return "Current password is incorrect"

                updates['password_hash'] = hash_password(updates['new_password'])
                del updates['current_password']
                del updates['new_password']

            if not updates:
                return "No valid fields to update"

            set_clause = ", ".join(f"{key} = %s" for key in updates)
            query = f"UPDATE users SET {set_clause} WHERE user_id = %s"
            cursor.execute(query, list(updates.values()) + [user_id])
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            return str(e)
        finally:
            cursor.close() 