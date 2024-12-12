import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', '113.198.66.75'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'xodbs1234'),
        database=os.getenv('DB_NAME', 'wsd3'),
        port=int(os.getenv('DB_PORT', '13145'))
    )

def run_migration():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 인덱스 SQL 파일 읽기
        with open('migrations/add_indexes.sql', 'r') as file:
            sql_commands = file.read().split(';')
            
        # 각 명령어 실행
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)
                print(f"Executed: {command[:50]}...")
        
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration() 