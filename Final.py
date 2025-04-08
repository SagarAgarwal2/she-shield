import tkinter as tk
from tkinter import messagebox, simpledialog
import mysql.connector
import cv2  # For camera access
import speech_recognition as sr  # For microphone access
import requests
from twilio.rest import Client
import geocoder  # For real-time location access
from datetime import datetime
import threading
import time
import geocoder
from geopy.distance import geodesic
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Email configuration
EMAIL_ADDRESS = 'unclepincle@gmail.com'  # Your Gmail address
EMAIL_PASSWORD = 'lder hlfg cnni fznd'  # Your Gmail App Password (not your regular password)
RECIPIENT_EMAIL = 'tnbtsper30@gmail.com'  # Email address to receive emergency alerts
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Global flag to stop capturing
stop_capture = False

# Database connection
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='sagar13',
            database='sheshield_db'
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error connecting to the database: {err}")
        return None

# Function to validate Aadhar number
def validate_aadhar(aadhar_number):
    if len(aadhar_number) != 12 or not aadhar_number.isdigit():
        return False
    return True


# Define a global variable to store the Aadhar number
aadhar_number_global = ""


# Function to request microphone access
def microphone_access():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Microphone access granted, you can say something...")
        audio = recognizer.listen(source)
        try:
            print(f"You said: {recognizer.recognize_google(audio)}")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("Microphone error")

def send_email(image_path):
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        print("Email settings not configured. Please configure email settings first.")
        return

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = 'Emergency Alert - Captured Image'
        
        # Get detailed location and time
        location = get_location()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create detailed email body
        body = f"""EMERGENCY ALERT - SheShield

Time: {current_time}
{location}

An emergency alert has been triggered. Please find the attached image captured by the safety app.
This is an automated message from SheShield - Women Safety App."""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the image
        try:
            with open(image_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(image_path)}')
                msg.attach(part)
        except Exception as e:
            print(f"Failed to attach image: {str(e)}")
            return
        
        # Send the email
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
            print(f"Email sent successfully with attachment: {image_path}")
        except smtplib.SMTPAuthenticationError:
            print("Email authentication failed. Please check your email settings and App Password.")
            return
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return
        
        # Clean up the image file after sending
        try:
            os.remove(image_path)
            print(f"Deleted local image file: {image_path}")
        except Exception as e:
            print(f"Could not delete local image file: {str(e)}")
            
    except Exception as e:
        print(f"Error in email sending process: {str(e)}")

# Continuous image capture function
def capture_images_continuously():
    global stop_capture
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        messagebox.showerror("Error", "Could not open webcam.")
        return

    # Create a window with a cancel button
    capture_window = tk.Toplevel(root)
    capture_window.title("Emergency Image Capture")
    capture_window.geometry("400x200")
    
    # Make the window stay on top
    capture_window.attributes('-topmost', True)
    
    # Add status label
    status_label = tk.Label(capture_window, text="Capturing images...", font=("Arial", 12))
    status_label.pack(pady=20)
    
    # Add cancel button
    cancel_button = tk.Button(capture_window, text="Stop Capture", 
                            command=lambda: [setattr(capture_images_continuously, 'stop_capture', True), capture_window.destroy()],
                            font=("Arial", 12), bg="red", fg="white")
    cancel_button.pack(pady=10)

    cv2.namedWindow("Continuous Capture")

    try:
        while True:
            if getattr(capture_images_continuously, 'stop_capture', False):
                print("Capture stopped by user.")
                break

            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame.")
                break

            # Display the current frame
            cv2.imshow("Continuous Capture", frame)

            # Save the current frame as an image
            img_name = f"captured_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(img_name, frame)
            print(f"{img_name} saved!")

            # Update status
            status_label.config(text=f"Last image captured: {datetime.now().strftime('%H:%M:%S')}")

            # Send the image via email
            try:
                send_email(img_name)
            except Exception as e:
                print(f"Failed to send email: {str(e)}")

            # Wait for 1 second before capturing the next frame
            time.sleep(1)

            # Check for ESC key to stop the capture
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                print("ESC pressed. Exiting...")
                break

    except Exception as e:
        print(f"Error in image capture: {str(e)}")
        messagebox.showerror("Error", f"Image capture error: {str(e)}")

    finally:
        cam.release()
        cv2.destroyAllWindows()
        if 'capture_window' in locals():
            capture_window.destroy()

# Function to start continuous image capture in a separate thread
def start_continuous_capture():
    global stop_capture
    stop_capture = False
    # Reset the stop_capture flag for the new capture session
    setattr(capture_images_continuously, 'stop_capture', False)
    capture_thread = threading.Thread(target=capture_images_continuously, daemon=True)
    capture_thread.start()

# Function to stop the continuous capture
def stop_continuous_capture():
    global stop_capture
    stop_capture = True

# Function to get real-time location
def get_location():
    try:
        # Try multiple location services for better accuracy
        location_data = {}
        
        # Method 1: IP-based location
        g_ip = geocoder.ip('me')
        if g_ip.ok:
            location_data['ip'] = {
                'lat': g_ip.latlng[0],
                'lng': g_ip.latlng[1],
                'address': g_ip.address if hasattr(g_ip, 'address') else None,
                'city': g_ip.city if hasattr(g_ip, 'city') else None,
                'state': g_ip.state if hasattr(g_ip, 'state') else None,
                'country': g_ip.country if hasattr(g_ip, 'country') else None
            }
        
        # Method 2: Try to get location from network
        try:
            g_network = geocoder.osm('me')
            if g_network.ok:
                location_data['network'] = {
                    'lat': g_network.latlng[0],
                    'lng': g_network.latlng[1],
                    'address': g_network.address if hasattr(g_network, 'address') else None,
                    'city': g_network.city if hasattr(g_network, 'city') else None,
                    'state': g_network.state if hasattr(g_network, 'state') else None,
                    'country': g_network.country if hasattr(g_network, 'country') else None
                }
        except:
            pass

        # Use the most accurate location data available
        if location_data:
            # Prefer network location if available, otherwise use IP location
            location = location_data.get('network', location_data.get('ip'))
            
            if location:
                lat, lng = location['lat'], location['lng']
                maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                
                # Format location information
                location_info = f"""Detailed Location Information:
Address: {location.get('address', 'Unknown address')}
City: {location.get('city', 'Unknown city')}
State: {location.get('state', 'Unknown state')}
Country: {location.get('country', 'Unknown country')}
Coordinates: {lat}, {lng}
Google Maps Link: {maps_link}
Accuracy: {'Network-based' if 'network' in location_data else 'IP-based'}"""
                
                return location_info
        
        return "Unable to get accurate location. Please check your internet connection."
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        return "Location service unavailable. Please check your internet connection."

# Function to send emergency SMS using Twilio
def send_emergency_sms(emergency_contacts):
    try:
        account_sid = 'AC16599e003f10804715efdefa20334ca2'
        auth_token = '53a8737b02d5975f4fa124127f3b52e7'
        client = Client(account_sid, auth_token)

        # Get detailed location
        location = get_location()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create detailed message
        message_body = f"""EMERGENCY ALERT - SheShield
Time: {current_time}
Location: {location}
This is an automated emergency alert. Please respond immediately."""

        for contact in emergency_contacts:
            try:
                message = client.messages.create(
                    body=message_body,
                    from_='+15165180831',
                    to=contact
                )
                print(f"SOS sent to {contact}")
            except Exception as e:
                if "unverified" in str(e).lower():
                    messagebox.showerror("Error", f"Could not send SMS to {contact}. This number needs to be verified in your Twilio account.")
                else:
                    messagebox.showerror("Error", f"Failed to send SMS to {contact}: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send emergency SMS: {str(e)}")

# Function to handle SOS feature
def open_sos_page():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()

        # Assuming aadhar_number_global is the unique identifier for the user logged in
        global aadhar_number_global

        cursor.execute("SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE aadhar=%s", (aadhar_number_global,))
        contacts = cursor.fetchone()

        if contacts:
            emergency_contacts = list(contacts)

            sos_window = tk.Toplevel(root)
            sos_window.title("SheShield - SOS")
            sos_window.geometry("400x400")

            tk.Label(sos_window, text="SOS Feature Activated", font=("Arial", 18), fg="red").pack(pady=20)

            # Emergency alert button functionality
            def emergency_alert():
                send_emergency_sms(emergency_contacts)
                print("Starting continuous image capture...")
                # Start continuous image capture when the emergency alert is triggered
                start_continuous_capture()

            # Request for microphone access
            microphone_access()  # Microphone access

            # Emergency alert button
            sos_button = tk.Button(sos_window, text="Press for Emergency Alert", command=emergency_alert, bg="red", fg="white", font=("Arial", 16))
            sos_button.pack(pady=20)

            sos_window.mainloop()

        else:
            messagebox.showerror("Error", "No emergency contacts found.")
        cursor.close()
        conn.close()

# Define safe zones (these can also be fetched from the database if needed)
safe_zones = [
    (28.6139, 77.2090),  # Example safe zone 1
    (28.7041, 77.1025)   # Example safe zone 2
]

# Function to fetch red zones from the MySQL database
def fetch_red_zones_from_db():
    try:
        # Establish connection to the MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='SOMYA@2004',  # Replace with your MySQL password
            database='sheshield_db'  # Replace with your database name
        )
        
        cursor = connection.cursor()
        # SQL query to fetch latitude and longitude of red zones
        cursor.execute("SELECT latitude, longitude FROM red_zones")
        
        # Fetch all rows
        red_zones = cursor.fetchall()
        
        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Convert the fetched data into a list of tuples
        return [(zone[0], zone[1]) for zone in red_zones]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

# Function to check if the user is inside any of the safe or red zones
def check_geofence(current_location):
    # Check if inside a safe zone
    for zone in safe_zones:
        distance = geodesic(current_location, zone).meters
        if distance <= 500:  # 500 meters radius for safe zone
            print(f"You are in a safe zone near {zone}.")
            return
    
    # Fetch red zones from the database
    red_zones = fetch_red_zones_from_db()
    
    # Check if near a red zone (based on incident reports)
    for zone in red_zones:
        distance = geodesic(current_location, zone).meters
        if distance <= 500:  # 500 meters radius for red zone
            print(f"Warning! You are near a red zone around {zone}.")
            return
    
    print("You are outside both safe and red zones.")

# Function to get the user's current location without Google Maps API
def get_current_location():
    g = geocoder.ip('me')  # Get location based on IP
    if g.ok:
        return (g.latlng[0], g.latlng[1])  # Return latitude and longitude
    else:
        print("Unable to retrieve current location.")
        return None

# Main execution
user_location = get_current_location()  # Get the user's current location
if user_location:
    check_geofence(user_location)
else:
    print("Could not determine current location.")






def create_account():
    def save_account():
        global aadhar_number_global
        name = entry_name.get()
        dob = entry_dob.get()
        mobile = entry_mobile.get()
        aadhar = entry_aadhar.get()

        # Aadhar validation
        if not validate_aadhar(aadhar):
            messagebox.showerror("Input Error", "Aadhar card number must be exactly 12 digits.")
            return

        # Save the Aadhar number to the global variable
        aadhar_number_global = aadhar
        
        # Save user data into the database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (name, dob, mobile, aadhar) VALUES (%s, %s, %s, %s)",
                           (name, dob, mobile, aadhar))
                conn.commit()
                messagebox.showinfo("Success", "Account created successfully!")
                account_window.destroy()  # Close the account window
                create_credentials()  # Open credentials window
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Error creating account: {err}")
            finally:
                cursor.close()
                conn.close()
    
    # Creating account page
    account_window = tk.Toplevel(root)
    account_window.title("Create Your Account")
    account_window.geometry("400x400")
    
    tk.Label(account_window, text="Name", font=("Arial", 14)).pack(pady=10)
    entry_name = tk.Entry(account_window, font=("Arial", 12))
    entry_name.pack()
    
    tk.Label(account_window, text="Date of Birth (YYYY-MM-DD)", font=("Arial", 14)).pack(pady=10)
    entry_dob = tk.Entry(account_window, font=("Arial", 12))
    entry_dob.pack()
    tk.Label(account_window, text="Format: YYYY-MM-DD", font=("Arial", 10), fg="red").pack(pady=5)

    tk.Label(account_window, text="Mobile Number", font=("Arial", 14)).pack(pady=10)
    entry_mobile = tk.Entry(account_window, font=("Arial", 12))
    entry_mobile.pack()

    tk.Label(account_window, text="Aadhar Card Number", font=("Arial", 14)).pack(pady=10)
    entry_aadhar = tk.Entry(account_window, font=("Arial", 12))
    entry_aadhar.pack()

    tk.Button(account_window, text="Submit", command=save_account, font=("Arial", 14), bg="green", fg="white").pack(pady=20)





# Function to create username and password
def create_credentials():
    def save_credentials():
        global aadhar_number_global
        username = entry_username.get()
        password = entry_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        # Save credentials into the database
        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET username=%s, password=%s WHERE aadhar=%s", 
                           (username, password, aadhar_number_global))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Success", "Account credentials saved successfully!")
                credentials_window.destroy()  # Close the credentials window
                add_emergency_contacts()  # Open emergency contacts window
            else:
                messagebox.showerror("Error", "Could not connect to database")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    credentials_window = tk.Toplevel(root)
    credentials_window.title("Set Username and Password")
    credentials_window.geometry("400x300")

    tk.Label(credentials_window, text="Create Username", font=("Arial", 14)).pack(pady=10)
    entry_username = tk.Entry(credentials_window, font=("Arial", 12))
    entry_username.pack()

    tk.Label(credentials_window, text="Create Password", font=("Arial", 14)).pack(pady=10)
    entry_password = tk.Entry(credentials_window, show="*", font=("Arial", 12))
    entry_password.pack()

    tk.Button(credentials_window, text="Save Credentials", command=save_credentials, font=("Arial", 14), bg="blue", fg="white").pack(pady=20)





# Function for login
def login():
    def check_login():
        username = entry_login_username.get()
        password = entry_login_password.get()

        conn = connect_db()  
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT aadhar FROM users WHERE username=%s AND password=%s", (username, password))
                result = cursor.fetchone()
                if result:
                    global aadhar_number_global
                    aadhar_number_global = result[0]
                    messagebox.showinfo("Login Success", "Welcome to SheShield!")
                    login_window.destroy()  # Close the login window
                    open_feature_page()  # Open the feature page after successful login
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password.")
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Database error: {err}")
            finally:
                cursor.close()
                conn.close()

    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.geometry("400x300")

    tk.Label(login_window, text="Enter Username", font=("Arial", 14)).pack(pady=10)
    entry_login_username = tk.Entry(login_window, font=("Arial", 12))
    entry_login_username.pack()

    tk.Label(login_window, text="Enter Password", font=("Arial", 14)).pack(pady=10)
    entry_login_password = tk.Entry(login_window, show="*", font=("Arial", 12))
    entry_login_password.pack()

    tk.Button(login_window, text="Login", command=check_login, font=("Arial", 14), bg="purple", fg="white").pack(pady=20)

# Function to open the feature page after successful login
def open_feature_page():
    feature_window = tk.Toplevel(root)
    feature_window.title("SheShield Features")
    feature_window.geometry("600x500")

    tk.Label(feature_window, text="Welcome to SheShield", font=("Arial", 20, "bold"), fg="purple").pack(pady=20)

    # Display the key features of the app
    tk.Label(feature_window, text="Key Features:", font=("Arial", 18), fg="blue").pack(pady=10)

    # Emergency alert with voice assistant
    tk.Label(feature_window, text="• Emergency Alert", font=("Arial", 14)).pack(anchor='w', padx=20)
    tk.Button(feature_window, text="Activate Emergency Alert", font=("Arial", 14), bg="red", fg="white", command=activate_emergency_alert).pack(pady=5)

    # Geofencing with safe zones and red zones
    tk.Label(feature_window, text="• Geofencing: Safe Zones & Red Zones", font=("Arial", 14)).pack(anchor='w', padx=20)
    tk.Button(feature_window, text="Enable Geofencing", font=("Arial", 14), bg="green", fg="white", command=enable_geofencing).pack(pady=5)

    # Local volunteer SMS alert
    tk.Label(feature_window, text="• Emergency SMS to Local Volunteer", font=("Arial", 14)).pack(anchor='w', padx=20)
    tk.Button(feature_window, text="Send Emergency SMS", font=("Arial", 14), bg="purple", fg="white", command=open_sos_page).pack(pady=5)

    # Email configuration
    tk.Label(feature_window, text="• Email Settings", font=("Arial", 14)).pack(anchor='w', padx=20)
    tk.Button(feature_window, text="Configure Email", font=("Arial", 14), bg="blue", fg="white", command=configure_email_settings).pack(pady=5)

# Button Function Definitions
''''def activate_emergency_alert():
    # Connect to the database
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        
        # Assuming aadhar_number_global is the unique identifier for the user logged in
        global aadhar_number_global

        # Fetch emergency contacts from the 'emergency_contacts' table based on user's aadhar number
        cursor.execute("SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE aadhar=%s", (aadhar_number_global,))
        contacts = cursor.fetchone()

        if contacts:
            emergency_contacts = [contact for contact in contacts if contact]  # Filter out None values

            if emergency_contacts:
                # Trigger the emergency alert
                messagebox.showinfo("Alert", "Emergency Alert activated!")

                # Send SMS to all emergency contacts
                send_emergency_sms(emergency_contacts)

                # Request microphone access
                microphone_access()

                # Start continuous image capture
                capture_images_continuously()
            else:
                messagebox.showerror("Error", "No emergency contacts found.")
        else:
            messagebox.showerror("Error", "No emergency contacts found for the user.")
        
        # Close the database connection
        cursor.close()
        conn.close()'''

def activate_emergency_alert():
    try:
        # Get emergency contacts from database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT contact1, contact2, contact3, contact4, contact5 FROM emergency_contacts WHERE aadhar=%s", (aadhar_number_global,))
            contacts = cursor.fetchone()
            cursor.close()
            conn.close()

            if contacts:
                # Filter out None values and format phone numbers
                emergency_contacts = []
                for contact in contacts:
                    if contact:
                        # Add country code if not present
                        if not contact.startswith('+'):
                            contact = '+91' + contact
                        emergency_contacts.append(contact)

                if emergency_contacts:
                    # Send SMS to all emergency contacts
                    send_emergency_sms(emergency_contacts)
                    
                    # Start image capture
                    start_continuous_capture()
                    
                    # Access microphone
                    microphone_access()
                    
                    messagebox.showinfo("Alert", "Emergency Alert activated! SMS sent and image capture started.")
                else:
                    messagebox.showerror("Error", "No valid emergency contacts found.")
            else:
                messagebox.showerror("Error", "No emergency contacts found in database.")
        else:
            messagebox.showerror("Error", "Could not connect to database.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to activate emergency alert: {str(e)}")

def enable_geofencing():
    # Logic to enable geofencing

    messagebox.showinfo("Geofencing", "Geofencing enabled with Safe and Red zones.")

# Function to create a new account
''''def create_account():
    create_window = tk.Toplevel(root)
    create_window.title("Create Account")
    create_window.geometry("400x300")

    tk.Label(create_window, text="Create Username", font=("Arial", 14)).pack(pady=10)
    entry_create_username = tk.Entry(create_window, font=("Arial", 12))
    entry_create_username.pack()

    tk.Label(create_window, text="Create Password", font=("Arial", 14)).pack(pady=10)
    entry_create_password = tk.Entry(create_window, show="*", font=("Arial", 12))
    entry_create_password.pack()

    def submit_account():
        username = entry_create_username.get()
        password = entry_create_password.get()
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                conn.commit()
                messagebox.showinfo("Success", "Account created successfully.")
                create_window.destroy()  # Close create account window
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Error creating account: {err}")
            cursor.close()
            conn.close()

    tk.Button(create_window, text="Submit", command=submit_account, font=("Arial", 14), bg="green", fg="white").pack(pady=20)''
    '''

# Main application
root = tk.Tk()
root.title("SheShield - Women Safety App")
root.geometry("400x400")

tk.Label(root, text="SheShield", font=("Arial", 24, "bold"), fg="purple").pack(pady=20)
tk.Label(root, text="Welcome to the Women Safety App", font=("Arial", 16)).pack(pady=10)

# Buttons for login and account creation
tk.Button(root, text="Login", command=login, font=("Arial", 14), bg="purple", fg="white").pack(pady=10)
tk.Button(root, text="Create New Account", command=create_account, font=("Arial", 14), bg="green", fg="white").pack(pady=10)

# Function to add emergency contacts
def add_emergency_contacts():
    def save_contacts():
        global aadhar_number_global
        contacts = [
            entry_contact1.get(),
            entry_contact2.get(),
            entry_contact3.get(),
            entry_contact4.get(),
            entry_contact5.get()
        ]
        
        # Validate phone numbers (basic validation)
        for contact in contacts:
            if contact and (not contact.isdigit() or len(contact) != 10):
                messagebox.showerror("Error", "Please enter valid 10-digit phone numbers")
                return
        
        # Save contacts to database
        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO emergency_contacts 
                    (aadhar, contact1, contact2, contact3, contact4, contact5) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (aadhar_number_global, *contacts))
                conn.commit()
                messagebox.showinfo("Success", "Emergency contacts saved successfully!")
                contacts_window.destroy()
                open_feature_page()  # Open the main feature page after setup is complete
            else:
                messagebox.showerror("Error", "Could not connect to database")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving contacts: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    # Create emergency contacts window
    contacts_window = tk.Toplevel(root)
    contacts_window.title("Add Emergency Contacts")
    contacts_window.geometry("400x500")
    contacts_window.transient(root)  # Make it stay on top of the main window

    tk.Label(contacts_window, text="Add Emergency Contacts", font=("Arial", 18, "bold"), fg="purple").pack(pady=20)
    tk.Label(contacts_window, text="Enter up to 5 emergency contact numbers", font=("Arial", 12)).pack(pady=10)

    # Create entry fields for contacts
    tk.Label(contacts_window, text="Contact 1 (Primary)", font=("Arial", 12)).pack(pady=5)
    entry_contact1 = tk.Entry(contacts_window, font=("Arial", 12))
    entry_contact1.pack()

    tk.Label(contacts_window, text="Contact 2", font=("Arial", 12)).pack(pady=5)
    entry_contact2 = tk.Entry(contacts_window, font=("Arial", 12))
    entry_contact2.pack()

    tk.Label(contacts_window, text="Contact 3", font=("Arial", 12)).pack(pady=5)
    entry_contact3 = tk.Entry(contacts_window, font=("Arial", 12))
    entry_contact3.pack()

    tk.Label(contacts_window, text="Contact 4", font=("Arial", 12)).pack(pady=5)
    entry_contact4 = tk.Entry(contacts_window, font=("Arial", 12))
    entry_contact4.pack()

    tk.Label(contacts_window, text="Contact 5", font=("Arial", 12)).pack(pady=5)
    entry_contact5 = tk.Entry(contacts_window, font=("Arial", 12))
    entry_contact5.pack()

    # Add save button
    tk.Button(contacts_window, text="Save Contacts", command=save_contacts, 
              font=("Arial", 14), bg="green", fg="white").pack(pady=20)

def configure_email_settings():
    def save_email_settings():
        global EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL
        EMAIL_ADDRESS = entry_email.get()
        EMAIL_PASSWORD = entry_password.get()
        RECIPIENT_EMAIL = entry_recipient.get()
        
        if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
            messagebox.showerror("Error", "Please fill in all email settings")
            return
            
        # Test email connection
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            messagebox.showinfo("Success", "Email settings saved and verified successfully!")
            email_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to verify email settings: {str(e)}\n\nPlease make sure:\n1. You're using Gmail\n2. You've enabled 2-Step Verification\n3. You're using an App Password")

    email_window = tk.Toplevel(root)
    email_window.title("Configure Email Settings")
    email_window.geometry("500x400")

    tk.Label(email_window, text="Email Configuration", font=("Arial", 18, "bold"), fg="purple").pack(pady=20)
    
    # Instructions
    instructions = """To use Gmail:
1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to Google Account > Security
   - Under '2-Step Verification', click 'App passwords'
   - Select 'Mail' and your device
   - Use the generated 16-character password below"""
    
    tk.Label(email_window, text=instructions, font=("Arial", 10), justify=tk.LEFT, wraplength=450).pack(pady=10)

    tk.Label(email_window, text="Your Gmail Address", font=("Arial", 12)).pack(pady=5)
    entry_email = tk.Entry(email_window, font=("Arial", 12))
    entry_email.pack()

    tk.Label(email_window, text="Gmail App Password", font=("Arial", 12)).pack(pady=5)
    entry_password = tk.Entry(email_window, show="*", font=("Arial", 12))
    entry_password.pack()

    tk.Label(email_window, text="Recipient Email", font=("Arial", 12)).pack(pady=5)
    entry_recipient = tk.Entry(email_window, font=("Arial", 12))
    entry_recipient.pack()

    tk.Button(email_window, text="Save Settings", command=save_email_settings, 
              font=("Arial", 14), bg="green", fg="white").pack(pady=20)

root.mainloop()
