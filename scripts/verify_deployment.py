#!/usr/bin/env python3
"""
Script to verify the Pupper deployment is working correctly
"""
import json
import requests
import time
import sys
import os

def test_endpoint(url, method="GET", data=None, expected_status=200, timeout=30):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        success = response.status_code == expected_status
        return {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "response": None,
            "error": str(e)
        }

def main():
    """Main verification function"""
    print("🔍 Verifying Pupper Deployment")
    print("=" * 40)
    
    # Get API URL from CDK outputs or environment
    api_url = None
    
    # Try to read from CDK outputs file
    if os.path.exists("cdk-outputs.json"):
        try:
            with open("cdk-outputs.json", "r") as f:
                outputs = json.load(f)
                # Look for API Gateway URL in outputs
                for stack_name, stack_outputs in outputs.items():
                    for key, value in stack_outputs.items():
                        if "api" in key.lower() and "url" in key.lower():
                            api_url = value.rstrip('/')
                            break
                    if api_url:
                        break
        except Exception as e:
            print(f"Warning: Could not read CDK outputs: {e}")
    
    # Fallback to environment variable
    if not api_url:
        api_url = os.environ.get('API_URL', 'http://localhost:3001')
    
    print(f"Testing API at: {api_url}")
    print()
    
    tests = [
        {
            "name": "Get all dogs",
            "url": f"{api_url}/dogs",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Get dogs with filter",
            "url": f"{api_url}/dogs?state=CA",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Create a test dog",
            "url": f"{api_url}/dogs",
            "method": "POST",
            "data": {
                "shelter_name": "Test Shelter",
                "city": "Test City",
                "state": "CA",
                "dog_name": "Test Dog",
                "dog_species": "Labrador Retriever",
                "shelter_entry_date": "1/1/2024",
                "dog_description": "A test dog for verification",
                "dog_birthday": "1/1/2020",
                "dog_weight": 50,
                "dog_color": "brown"
            },
            "expected_status": 200
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"Testing: {test['name']}")
        result = test_endpoint(
            test["url"],
            test.get("method", "GET"),
            test.get("data"),
            test.get("expected_status", 200)
        )
        
        if result["success"]:
            print(f"  ✅ PASS (Status: {result['status_code']})")
            if test["name"] == "Get all dogs" and result["response"]:
                try:
                    dog_count = result["response"]["data"]["count"]
                    print(f"     Found {dog_count} dogs in database")
                except:
                    pass
        else:
            print(f"  ❌ FAIL (Status: {result.get('status_code', 'N/A')})")
            if result["error"]:
                print(f"     Error: {result['error']}")
            elif result["response"]:
                print(f"     Response: {result['response']}")
        
        results.append(result)
        print()
    
    # Summary
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Pupper deployment is working correctly.")
        
        print("\nNext steps:")
        print("1. Run the test data population script:")
        print(f"   python3 scripts/populate_test_data.py")
        print("2. Deploy and configure the frontend application")
        print("3. Test the complete user workflow")
        
        return 0
    else:
        print("❌ Some tests failed. Please check the deployment and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
