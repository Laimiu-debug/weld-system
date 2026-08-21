"""
Test script for WPS templates API endpoint
"""
import requests
import json
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

# Get user
db = SessionLocal()
user = db.query(User).filter(User.email == "testuser176070001@example.com").first()

if not user:
    print("User not found!")
    exit(1)

print(f"User found: {user.email} (ID: {user.id})")
print(f"User is_verified: {user.is_verified}")
print(f"User is_active: {user.is_active}")

# Create access token
token = create_access_token(subject=str(user.id))
print(f"\nAccess token: {token[:50]}...")

# Test the endpoint
url = "http://localhost:8000/api/v1/wps-templates/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"\nTesting GET {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess! Got {data.get('total', 0)} templates")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"\nError Response:")
        print(response.text)
except Exception as e:
    print(f"\nException occurred: {e}")
finally:
    db.close()

