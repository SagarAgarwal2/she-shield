import streamlit as st
import mysql.connector
import cv2
import numpy as np
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
import os
from datetime import datetime
import geocoder
import time
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="SheShield - Women Safety App",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .emergency-button {
        background-color: #ff4444 !important;
        color: white !important;
        font-size: 1.5em !important;
    }
    .sidebar .sidebar-content {
        background-color: #2c3e50;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .stSelectbox>div>div>select {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'sagar13'),
            database=os.getenv('DB_NAME', 'sheshield_db')
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Authentication functions
def login(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user['id']
                st.success("Login successful!")
                return True
            else:
                st.error("Invalid credentials")
                return False
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def register(name, dob, mobile, aadhar, username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, dob, mobile, aadhar, username, password) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, dob, mobile, aadhar, username, password)
            )
            conn.commit()
            st.success("Registration successful! Please login.")
            return True
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

# Emergency functions
def send_emergency_sms(contacts):
    try:
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        location = get_location()
        message = f"EMERGENCY ALERT! Your contact needs help!\nLocation: {location}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        for contact in contacts:
            if contact:
                client.messages.create(
                    body=message,
                    from_=os.getenv('TWILIO_PHONE_NUMBER'),
                    to=contact
                )
        return True
    except Exception as e:
        st.error(f"Error sending SMS: {e}")
        return False

def get_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            return f"https://www.google.com/maps?q={g.latlng[0]},{g.latlng[1]}"
        return "Location unavailable"
    except Exception as e:
        return "Location unavailable"

def capture_and_send_image():
    try:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Could not open camera")
            return False
        
        # Capture image
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture image")
            return False
        
        # Save image
        image_path = f"emergency_{st.session_state.user_id}_{int(time.time())}.jpg"
        cv2.imwrite(image_path, frame)
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_ADDRESS')
        msg['To'] = os.getenv('RECIPIENT_EMAIL')
        msg['Subject'] = 'Emergency Alert - Image Capture'
        
        body = f"Emergency alert triggered!\nLocation: {get_location()}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg.attach(MIMEText(body))
        
        with open(image_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
            msg.attach(img)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
        
        os.remove(image_path)
        cap.release()
        return True
    except Exception as e:
        st.error(f"Error capturing and sending image: {e}")
        return False

# Main app
def main():
    st.title("🛡️ SheShield - Women Safety App")
    
    if not st.session_state.logged_in:
        # Authentication section
        auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
        
        with auth_tab1:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
        
        with auth_tab2:
            st.subheader("Register")
            name = st.text_input("Name")
            dob = st.date_input("Date of Birth")
            mobile = st.text_input("Mobile Number")
            aadhar = st.text_input("Aadhar Card Number")
            username = st.text_input("Choose Username")
            password = st.text_input("Choose Password", type="password")
            if st.button("Register"):
                register(name, dob, mobile, aadhar, username, password)
    
    else:
        # Main application
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Dashboard", "Emergency Contacts", "Settings"])
        
        if page == "Dashboard":
            st.header("Dashboard")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Emergency Alert")
                if st.button("🚨 SOS Emergency", key="sos", use_container_width=True, 
                           help="Press in case of emergency"):
                    # Get emergency contacts
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE user_id = %s",
                            (st.session_state.user_id,)
                        )
                        contacts = cursor.fetchone()
                        cursor.close()
                        conn.close()
                        
                        if contacts:
                            # Send SMS
                            if send_emergency_sms(contacts):
                                st.success("Emergency alert sent successfully!")
                            # Capture and send image
                            if capture_and_send_image():
                                st.success("Emergency image captured and sent!")
                        else:
                            st.warning("No emergency contacts found. Please add contacts in the Emergency Contacts section.")
            
            with col2:
                st.subheader("Location")
                location = get_location()
                st.write(f"Current Location: {location}")
                if st.button("Refresh Location"):
                    location = get_location()
                    st.write(f"Updated Location: {location}")
        
        elif page == "Emergency Contacts":
            st.header("Emergency Contacts")
            st.write("Add up to 5 emergency contacts")
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE user_id = %s",
                    (st.session_state.user_id,)
                )
                existing_contacts = cursor.fetchone()
                cursor.close()
                
                if existing_contacts:
                    st.write("Current Emergency Contacts:")
                    for i, contact in enumerate(existing_contacts, 1):
                        if contact:
                            st.write(f"Contact {i}: {contact}")
                
                with st.form("emergency_contacts_form"):
                    contacts = []
                    for i in range(5):
                        contacts.append(st.text_input(f"Contact {i+1} Phone Number", 
                                                    value=existing_contacts[i] if existing_contacts else ""))
                    
                    if st.form_submit_button("Save Contacts"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO emergency_contacts (user_id, contact1, contact2, contact3, contact4, contact5) "
                            "VALUES (%s, %s, %s, %s, %s, %s) "
                            "ON DUPLICATE KEY UPDATE contact1 = VALUES(contact1), contact2 = VALUES(contact2), "
                            "contact3 = VALUES(contact3), contact4 = VALUES(contact4), contact5 = VALUES(contact5)",
                            (st.session_state.user_id, *contacts)
                        )
                        conn.commit()
                        cursor.close()
                        st.success("Emergency contacts saved successfully!")
                conn.close()
        
        elif page == "Settings":
            st.header("Settings")
            st.subheader("Email Configuration")
            
            with st.form("email_settings_form"):
                email = st.text_input("Email Address", value=os.getenv('EMAIL_ADDRESS', ''))
                email_password = st.text_input("Email Password", type="password", value=os.getenv('EMAIL_PASSWORD', ''))
                recipient_email = st.text_input("Recipient Email", value=os.getenv('RECIPIENT_EMAIL', ''))
                
                if st.form_submit_button("Save Settings"):
                    # Update environment variables
                    os.environ['EMAIL_ADDRESS'] = email
                    os.environ['EMAIL_PASSWORD'] = email_password
                    os.environ['RECIPIENT_EMAIL'] = recipient_email
                    st.success("Email settings saved successfully!")

if __name__ == "__main__":
    main() 