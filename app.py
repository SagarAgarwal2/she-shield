from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
import json
import time
import logging
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'sagar13'),
    'database': os.getenv('DB_NAME', 'sheshield_db')
}

# Twilio configuration
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Email configuration
EMAIL_CONFIG = {
    'address': os.getenv('EMAIL_ADDRESS'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'recipient': os.getenv('RECIPIENT_EMAIL')
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        logger.debug("Database connection successful")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

@app.route('/')
def index():
    logger.debug("Rendering index page")
    return render_template('index.html')

@app.route('/check_login')
def check_login():
    return jsonify({'logged_in': 'user_id' in session})

@app.route('/login', methods=['POST'])
def login():
    logger.debug("Login attempt")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            logger.debug(f"User {username} logged in successfully")
            return jsonify({'success': True})
        else:
            logger.debug(f"Invalid login attempt for username: {username}")
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    except mysql.connector.Error as err:
        logger.error(f"Database error during login: {err}")
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    dob = data.get('dob')
    mobile = data.get('mobile')
    aadhar = data.get('aadhar')
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, dob, mobile, aadhar, username, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, dob, mobile, aadhar, username, password)
        )
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/emergency', methods=['POST'])
def emergency():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE user_id = %s",
            (session['user_id'],)
        )
        contacts = cursor.fetchone()

        if contacts:
            # Send SMS to all contacts
            for contact in contacts:
                if contact:
                    try:
                        twilio_client.messages.create(
                            body="EMERGENCY ALERT: Your contact has triggered an emergency alert. Please check on them immediately.",
                            from_=os.getenv('TWILIO_PHONE_NUMBER'),
                            to=contact
                        )
                    except Exception as e:
                        logger.error(f"Error sending SMS to {contact}: {e}")

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'No emergency contacts found'})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/capture', methods=['POST'])
def capture():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({'success': False, 'message': 'No image data received'})

    try:
        # Convert base64 image to OpenCV format
        image_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Save image to file
        image_path = f"static/images/emergency_{session['user_id']}_{int(time.time())}.jpg"
        cv2.imwrite(image_path, img)

        # Send email with image
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['address']
        msg['To'] = EMAIL_CONFIG['recipient']
        msg['Subject'] = 'Emergency Alert - Image Capture'

        body = "An emergency alert has been triggered. Please find the attached image."
        msg.attach(MIMEText(body))

        with open(image_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
            msg.attach(img)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(msg)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'})

@app.route('/location', methods=['POST'])
def location():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    try:
        # Get location from request
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not latitude or not longitude:
            return jsonify({'success': False, 'message': 'Invalid location data'})

        # Save location to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'})

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO location_history (user_id, latitude, longitude, timestamp) VALUES (%s, %s, %s, %s)",
            (session['user_id'], latitude, longitude, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error processing location: {e}")
        return jsonify({'success': False, 'message': f'Error processing location: {str(e)}'})

@app.route('/contacts', methods=['POST'])
def save_contacts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    contacts = [
        data.get('contact1'),
        data.get('contact2'),
        data.get('contact3'),
        data.get('contact4'),
        data.get('contact5')
    ]

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO emergency_contacts (user_id, contact1, contact2, contact3, contact4, contact5) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE contact1 = VALUES(contact1), contact2 = VALUES(contact2), contact3 = VALUES(contact3), contact4 = VALUES(contact4), contact5 = VALUES(contact5)",
            (session['user_id'], *contacts)
        )
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        cursor.close()
        conn.close()

@app.route('/settings', methods=['POST'])
def save_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    recipient = data.get('recipient')

    if not all([email, password, recipient]):
        return jsonify({'success': False, 'message': 'All fields are required'})

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO email_settings (user_id, email, password, recipient) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE email = VALUES(email), password = VALUES(password), recipient = VALUES(recipient)",
            (session['user_id'], email, password, recipient)
        )
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    logger.debug("Starting Flask application")
    app.run(debug=True)