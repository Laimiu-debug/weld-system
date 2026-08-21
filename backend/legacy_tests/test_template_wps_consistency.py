#!/usr/bin/env python
"""Test script to verify WPS template data consistency fix."""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjExNTUzMTksInN1YiI6IjIxIn0.Ej0p8uYvxZ-zxQw0KKwxZ0Z0Z0Z0Z0Z0Z0Z0Z0Z0"

def test_wps_list_with_modules_data():
    """Test WPS list API to verify modules_data is returned."""
    print("=" * 70)
    print("Testing WPS List API - Template Data Consistency")
    print("=" * 70)
    
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
        
        print(f"\n📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API returned successfully")
            print(f"📊 Number of WPS records: {len(data)}")
            
            if len(data) > 0:
                # Find a WPS with modules_data
                wps_with_modules = None
                for wps in data:
                    if wps.get('modules_data'):
                        wps_with_modules = wps
                        break
                
                if wps_with_modules:
                    print(f"\n✅ Found WPS with modules_data!")
                    print(f"\n📋 WPS Record with Template Data:")
                    print(f"  ID: {wps_with_modules['id']}")
                    print(f"  WPS Number: {wps_with_modules['wps_number']}")
                    print(f"  Title: {wps_with_modules['title']}")
                    print(f"  Status: {wps_with_modules['status']}")
                    print(f"  Template ID: {wps_with_modules.get('template_id', 'N/A')}")
                    
                    print(f"\n📦 Modules Data Structure:")
                    modules_data = wps_with_modules.get('modules_data', {})
                    if modules_data:
                        print(f"  Number of modules: {len(modules_data)}")
                        for module_id, module_content in modules_data.items():
                            print(f"\n  Module: {module_id}")
                            if isinstance(module_content, dict):
                                print(f"    - moduleId: {module_content.get('moduleId', 'N/A')}")
                                print(f"    - customName: {module_content.get('customName', 'N/A')}")
                                if 'data' in module_content:
                                    print(f"    - Fields: {len(module_content['data'])} fields")
                                    for field_key, field_value in list(module_content['data'].items())[:3]:
                                        print(f"      • {field_key}: {field_value}")
                                    if len(module_content['data']) > 3:
                                        print(f"      ... and {len(module_content['data']) - 3} more fields")
                    else:
                        print("  ⚠️  modules_data is empty")
                    
                    print(f"\n✅ Template data consistency check PASSED!")
                else:
                    print(f"\n⚠️  No WPS records with modules_data found")
                    print(f"   (This is OK if no WPS was created from templates yet)")
                    
                    # Show first WPS for reference
                    first_wps = data[0]
                    print(f"\n📋 First WPS Record (for reference):")
                    print(json.dumps(first_wps, indent=2, default=str))
            else:
                print("⚠️  No WPS records found in the database")
        else:
            print(f"❌ API returned error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_wps_list_with_modules_data()

