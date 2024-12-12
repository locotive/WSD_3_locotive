from app.database import get_db
from app.auth.utils import base64_encode_password, create_access_token, create_refresh_token

class User:
    @staticmethod
    def create_user(email: str, password: str, name: str, phone: str = None, birth_date: str = None):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                return None, "Email already registered"

            hashed_pw = base64_encode_password(password)

            cursor.execute(
                """
                INSERT INTO users(email, password_hash, name, phone, birth_date, status) 
                VALUES (%s, %s, %s, %s, %s, 'active')
                """,
                (email, hashed_pw, name, phone, birth_date)
            )
            db.commit()
            user_id = cursor.lastrowid

            access_token = create_access_token(data={"sub": str(user_id)})
            refresh_token = create_refresh_token(data={"sub": str(user_id)})

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }, None

        except Exception as e:
            db.rollback()
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

            if not base64_encode_password(password) == user['password_hash']:
                return None, "Invalid credentials"

            access_token = create_access_token(data={"sub": str(user['user_id'])})
            refresh_token = create_refresh_token(data={"sub": str(user['user_id'])})

            cursor.execute(
                "UPDATE users SET last_login=NOW() WHERE user_id=%s",
                (user['user_id'],)
            )
            db.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
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

                if not base64_encode_password(updates['current_password']) == current_hash:
                    return "Current password is incorrect"

                updates['password_hash'] = base64_encode_password(updates['new_password'])
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