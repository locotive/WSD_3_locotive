from app.database import get_db
from app.auth.utils import hash_password, verify_password, generate_tokens
import logging
from datetime import datetime

class User:
    @staticmethod
    def create_user(email: str, password: str, name: str, phone: str = None, birth_date: str = None):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT user_id FROM users 
                WHERE email = %s AND status = 'active'
            """, (email,))
            
            if cursor.fetchone():
                return None, "Email already registered"

            hashed_pw = hash_password(password)

            birth_date_obj = None
            if birth_date:
                try:
                    birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    return None, "Invalid birth date format. Use YYYY-MM-DD"

            cursor.execute("""
                INSERT INTO users (
                    email, 
                    password_hash, 
                    name, 
                    phone, 
                    birth_date, 
                    status
                ) VALUES (%s, %s, %s, %s, %s, 'active')
            """, (
                email,
                hashed_pw,
                name,
                phone,
                birth_date_obj
            ))
            
            db.commit()
            user_id = cursor.lastrowid

            cursor.execute("""
                SELECT 
                    user_id,
                    email,
                    name,
                    phone,
                    birth_date,
                    created_at
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            
            user_data = cursor.fetchone()
            
            if not user_data:
                return None, "Failed to create user"

            tokens = generate_tokens(user_id)

            return {
                "user_id": user_data['user_id'],
                "email": user_data['email'],
                "name": user_data['name'],
                "access_token": tokens['access_token'],
                "token_type": "bearer",
                "created_at": user_data['created_at'].isoformat()
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

    @staticmethod
    def delete_user(user_id: int):
        db = get_db()
        cursor = db.cursor()

        try:
            # 사용자 상태를 'inactive'로 변경
            cursor.execute("""
                UPDATE users 
                SET status = 'inactive' 
                WHERE user_id = %s AND status = 'active'
            """, (user_id,))
            
            if cursor.rowcount == 0:
                return "User not found or already inactive"

            # 관련 데이터 처리
            # 지원 내역 상태 변경
            cursor.execute("""
                UPDATE applications 
                SET status = 'cancelled' 
                WHERE user_id = %s AND status = 'pending'
            """, (user_id,))

            # 북마크 삭제
            cursor.execute("DELETE FROM bookmarks WHERE user_id = %s", (user_id,))

            db.commit()
            return None

        except Exception as e:
            db.rollback()
            logging.error(f"User deletion error: {str(e)}")
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_user_profile(user_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT 
                    user_id,
                    email,
                    name,
                    phone,
                    birth_date,
                    created_at,
                    last_login,
                    (SELECT COUNT(*) FROM applications WHERE user_id = users.user_id) as application_count,
                    (SELECT COUNT(*) FROM bookmarks WHERE user_id = users.user_id) as bookmark_count
                FROM users
                WHERE user_id = %s AND status = 'active'
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return None, "User not found"

            return user, None

        except Exception as e:
            logging.error(f"Profile fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close() 