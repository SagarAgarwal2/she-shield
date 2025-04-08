import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'sagar13'),
}

def setup_database():
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Read and execute SQL script
        with open('setup_database.sql', 'r') as file:
            sql_script = file.read()
        
        # Split the script into individual statements
        statements = sql_script.split(';')
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        print("Database setup completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error setting up database: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    setup_database() 