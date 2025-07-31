import gspread
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_google_sheets():
    try:
        print("Testing Google Sheets connection...")
        
        # Check if credentials file exists
        if not os.path.exists('credentials.json'):
            print("❌ credentials.json file not found!")
            print("Please download it from Google Cloud Console and place it in the same folder")
            return
        
        print("✅ credentials.json found")
        
        # Test connection
        gc = gspread.service_account(filename='credentials.json')
        print("✅ Google Sheets authentication successful")
        
        # Test opening the sheet
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        print(f"Trying to open sheet ID: {sheet_id}")
        
        sheet = gc.open_by_key(sheet_id).sheet1
        print("✅ Successfully opened Google Sheet")
        
        # Test writing data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_data = [timestamp, "test@example.com", "/test", "test_success"]
        
        # Check if sheet has headers
        all_records = sheet.get_all_records()
        if not all_records:
            print("Adding header row...")
            sheet.append_row(['Timestamp', 'Email', 'Source Page', 'Status'])
        
        print("Adding test row...")
        sheet.append_row(test_data)
        print("✅ Successfully wrote test data to Google Sheets")
        
        # Verify the data was written
        last_row = sheet.get_all_values()[-1]
        print(f"Last row in sheet: {last_row}")
        
    except Exception as e:
        print(f"❌ Google Sheets Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure credentials.json is in the same folder as app.py")
        print("2. Verify the Google Sheet ID in .env file")
        print("3. Share the Google Sheet with the service account email")

if __name__ == "__main__":
    test_google_sheets()