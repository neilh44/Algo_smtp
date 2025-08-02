from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import smtplib
import gspread
import validators
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Development CORS - allow all origins
CORS(app, 
     origins="*",  # Allow all origins for development
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'Accept']
)

logger.info("Flask app initialized successfully")

# Read email template from external file
def load_email_template():
    """Load HTML email template from external file"""
    try:
        with open('email_template.html', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error("email_template.html not found. Please ensure the file exists in the project root.")
        # Fallback to a simple template
        return """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>🎉 Welcome to AutomateAlgos!</h2>
        <p>Thank you for joining us! Your exclusive bonuses are ready.</p>
        <a href="https://automatealgos.in/bonus" style="background: #10b981; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
            Access Your Bonuses
        </a>
        </body>
        </html>
        """

# Load template once at startup
EMAIL_TEMPLATE = load_email_template()

def send_email(to_email):
    """Send HTML email via Gmail SMTP"""
    try:
        logger.info(f"Attempting to send email to: {to_email}")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎁 Your Free Trading Bonuses Worth ₹24,493 Are Here!"
        msg['From'] = os.getenv('GMAIL_USER')
        msg['To'] = to_email
        
        # Use the loaded HTML template
        html_part = MIMEText(EMAIL_TEMPLATE, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to: {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email sending failed for {to_email}: {str(e)}")
        return False

def log_to_sheets(email, source_page, status):
    """Log submission to Google Sheets"""
    try:
        logger.info(f"Logging to sheets: {email} from {source_page} with status {status}")
        
        # Use service account JSON file
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_ID')).sheet1
        
        # Add header row if sheet is empty
        if not sheet.get_all_records():
            sheet.append_row(['Timestamp', 'Email', 'Source Page', 'Status'])
            logger.info("Added header row to Google Sheet")
        
        # Add new row
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.append_row([timestamp, email, source_page, status])
        
        logger.info(f"Successfully logged to Google Sheets: {email}")
        return True
    except Exception as e:
        logger.error(f"Google Sheets logging failed for {email}: {str(e)}")
        return False

@app.route('/api/popup-submit', methods=['POST', 'OPTIONS'])
def popup_submit():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        logger.info("OPTIONS preflight request received")
        return '', 200
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    try:
        logger.info(f"POST request received from IP: {client_ip}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        email = data.get('email', '').strip().lower()
        source_page = data.get('source_page', '')
        
        logger.info(f"Popup submission received - Email: {email}, Source: {source_page}, IP: {client_ip}")
        
        # Validate email
        if not email or not validators.email(email):
            logger.warning(f"Invalid email submission: {email} from IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Invalid email'}), 400
        
        # Send email
        email_sent = send_email(email)
        
        # Log to sheets
        status = 'success' if email_sent else 'email_failed'
        sheets_logged = log_to_sheets(email, source_page, status)
        
        if email_sent:
            logger.info(f"Successful submission - Email: {email}, Sheets logged: {sheets_logged}")
            return jsonify({
                'success': True, 
                'message': 'Email sent successfully',
                'sheets_logged': sheets_logged
            })
        else:
            logger.error(f"Failed submission - Email sending failed for: {email}")
            return jsonify({'success': False, 'error': 'Failed to send email'}), 500
            
    except Exception as e:
        logger.error(f"API error for IP {client_ip}: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Bind to 0.0.0.0 to allow external connections (required for Render)
    logger.info(f"Starting Flask application on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
