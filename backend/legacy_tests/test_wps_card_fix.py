#!/usr/bin/env python
"""Test script to verify WPS card display fix."""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjExNTUzMTksInN1YiI6IjIxIn0.Ej0p8uYvxZ-zxQw0KKwxZ0Z0Z0Z0Z0Z0Z0Z0Z0Z0"

def test_wps_list_api():
    """Test WPS list API to verify filler_material_classification is returned."""
    print("=" * 60)
    print("Testing WPS List API")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "X-Workspace-ID": "enterprise"
    }
    
    params = {
        "skip": 0,
        "limit": 20
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/wps/",
            headers=headers,
            params=params,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API returned successfully")
            print(f"Number of WPS records: {len(data)}")
            
            if len(data) > 0:
                first_wps = data[0]
                print(f"\n📋 First WPS Record:")
                print(json.dumps(first_wps, indent=2, default=str))
                
                # Check for required fields
                required_fields = [
                    'id', 'title', 'wps_number', 'revision', 'status',
                    'company', 'project_name', 'welding_process',
                    'base_material_spec', 'filler_material_classification',
                    'created_at', 'updated_at'
                ]
                
                print(f"\n🔍 Field Verification:")
                for field in required_fields:
                    if field in first_wps:
                        value = first_wps[field]
                        print(f"  ✅ {field}: {value}")
                    else:
                        print(f"  ❌ {field}: MISSING")
                
                # Check if filler_material_classification is present
                if 'filler_material_classification' in first_wps:
                    print(f"\n✅ filler_material_classification field is present!")
                    print(f"   Value: {first_wps['filler_material_classification']}")
                else:
                    print(f"\n❌ filler_material_classification field is MISSING!")
            else:
                print("⚠️  No WPS records found in the database")
        else:
            print(f"❌ API returned error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_wps_list_api()

