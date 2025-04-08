import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'sheshield')
        )
        print("Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    test_db_connection() 