# SheShield - Women Safety App

A comprehensive women safety application with emergency alerts, location tracking, and contact management.

## Features

- User Authentication (Login/Register)
- Emergency SOS Button
- Location Tracking
- Emergency Image Capture
- Emergency Contacts Management
- Email Notifications
- SMS Alerts (via Twilio)

## Setup Instructions

1. **Database Setup**
   - Install MySQL if not already installed
   - Create a new database using the provided SQL script:
     ```bash
     mysql -u root -p < setup_database.sql
     ```

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Update the following variables in `.env`:
     - `DB_HOST`: Your MySQL host (default: localhost)
     - `DB_USER`: Your MySQL username
     - `DB_PASSWORD`: Your MySQL password
     - `DB_NAME`: Database name (default: sheshield_db)
     - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
     - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
     - `TWILIO_PHONE_NUMBER`: Your Twilio phone number

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Application**
   - Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Registration**
   - Click on the "Register" tab
   - Fill in your details (username, email, password)
   - Submit the form to create your account

2. **Login**
   - Enter your username and password
   - Click "Login" to access your dashboard

3. **Dashboard**
   - Emergency SOS Button: Click to send emergency alerts
   - Location: View and update your current location
   - Camera: Capture and send emergency photos

4. **Emergency Contacts**
   - Add up to 5 emergency contacts
   - Include name, phone number, and relationship
   - Contacts will receive alerts during emergencies

5. **Settings**
   - Configure email and SMS notification preferences
   - Update your account settings

## Security Features

- Password hashing for secure authentication
- Session management
- Secure database connections
- Input validation and sanitization
- Error handling and logging

## Troubleshooting

1. **Database Connection Issues**
   - Verify database credentials in `.env`
   - Ensure MySQL service is running
   - Check database permissions

2. **Email/SMS Notifications Not Working**
   - Verify Twilio credentials in `.env`
   - Check internet connection
   - Verify email server settings

3. **Location Services Not Working**
   - Ensure browser has location permissions
   - Check internet connection
   - Verify GPS is enabled on mobile devices

## Support

For any issues or questions, please contact the development team. 