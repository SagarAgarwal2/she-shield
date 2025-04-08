import tkinter as tk
import cv2
from datetime import datetime
import threading
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Global flag to stop capturing
stop_capture = False

# Email configuration
EMAIL_ADDRESS = ''  # Replace with your email address
EMAIL_PASSWORD = ''  # Replace with your email password
RECIPIENT_EMAIL = ''  # Replace with the recipient's email address
SMTP_SERVER = 'smtp.gmail.com'  # Replace with your SMTP server (e.g., 'smtp.gmail.com' for Gmail)
SMTP_PORT = 587  # Replace with your SMTP port (587 for TLS)

def send_email(image_path):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = 'Captured Image'
    
    body = 'Please find the attached image captured by the safety app.'
    msg.attach(MIMEText(body, 'plain'))
    
    attachment = open(image_path, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(image_path)}')
    msg.attach(part)
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    print(f"Email sent with attachment: {image_path}")

# Function to continuously capture images and send via email
def capture_images_continuously():
    global stop_capture
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Could not open webcam.")
        return

    cv2.namedWindow("Continuous Capture")

    try:
        while True:
            if stop_capture:
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

            # Send the image via email
            #send_email(img_name)

            # Wait for 1 second before capturing the next frame
            time.sleep(1)

            # Check for ESC key to stop the capture
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                print("ESC pressed. Exiting...")
                break

    except KeyboardInterrupt:
        print("Continuous capture interrupted.")

    finally:
        cam.release()
        cv2.destroyAllWindows()

# Function to start continuous image capture in a separate thread
def start_continuous_capture():
    global stop_capture
    stop_capture = False
    capture_thread = threading.Thread(target=capture_images_continuously)
    capture_thread.start()

# Function to stop the continuous capture
def stop_continuous_capture():
    global stop_capture
    stop_capture = True

# Tkinter GUI for Image Capture Button
def image_capture_gui():
    root = tk.Tk()
    root.title("Women Safety App")

    capture_button = tk.Button(root, text="Start Continuous Capture", command=start_continuous_capture)
    capture_button.pack(pady=20)

    stop_button = tk.Button(root, text="Stop Capture", command=stop_continuous_capture)
    stop_button.pack(pady=20)

    root.mainloop()

# Run the Tkinter GUI
image_capture_gui()
