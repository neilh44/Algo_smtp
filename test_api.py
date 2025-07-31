import requests
import json

# Test the Flask API directly
url = "http://127.0.0.1:5000/api/popup-submit"

data = {
    "email": "hanotianilesh@gmail.com",
    "source_page": "/test"
}

try:
    print("Testing Flask API...")
    response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")