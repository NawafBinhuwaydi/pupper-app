#!/usr/bin/env python3
"""
Script to populate the Pupper application with test data
"""
import json
import requests
import base64
from datetime import datetime, timedelta
import random
import os

# Test data
TEST_DOGS = [
    {
        "shelter_name": "Arlington Animal Shelter",
        "city": "Arlington",
        "state": "VA",
        "dog_name": "Buddy",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "1/15/2024",
        "dog_description": "Buddy is a friendly and energetic Labrador who loves to play fetch and go for long walks. He's great with kids and other dogs, making him the perfect family companion.",
        "dog_birthday": "3/10/2020",
        "dog_weight": 65,
        "dog_color": "yellow"
    },
    {
        "shelter_name": "Golden Gate Animal Rescue",
        "city": "San Francisco",
        "state": "CA",
        "dog_name": "Luna",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "2/3/2024",
        "dog_description": "Luna is a gentle and loving chocolate Lab who enjoys swimming and hiking. She's well-trained and would make an excellent companion for an active family.",
        "dog_birthday": "7/22/2019",
        "dog_weight": 58,
        "dog_color": "chocolate"
    },
    {
        "shelter_name": "Austin Pet Rescue",
        "city": "Austin",
        "state": "TX",
        "dog_name": "Max",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "12/20/2023",
        "dog_description": "Max is a playful black Lab puppy who loves everyone he meets. He's still learning basic commands but is very eager to please and quick to learn.",
        "dog_birthday": "5/8/2023",
        "dog_weight": 45,
        "dog_color": "black"
    },
    {
        "shelter_name": "Miami Animal Services",
        "city": "Miami",
        "state": "FL",
        "dog_name": "Bella",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "1/28/2024",
        "dog_description": "Bella is a sweet and calm yellow Lab who loves to cuddle and relax. She's perfect for a family looking for a more laid-back companion who still enjoys daily walks.",
        "dog_birthday": "11/15/2018",
        "dog_weight": 52,
        "dog_color": "yellow"
    },
    {
        "shelter_name": "Seattle Humane Society",
        "city": "Seattle",
        "state": "WA",
        "dog_name": "Charlie",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "2/10/2024",
        "dog_description": "Charlie is an adventurous chocolate Lab who loves outdoor activities. He's great with children and has a gentle temperament that makes him perfect for families.",
        "dog_birthday": "9/3/2021",
        "dog_weight": 72,
        "dog_color": "chocolate"
    },
    {
        "shelter_name": "Denver Animal Shelter",
        "city": "Denver",
        "state": "CO",
        "dog_name": "Daisy",
        "dog_species": "Labrador Retriever",
        "shelter_entry_date": "1/5/2024",
        "dog_description": "Daisy is a beautiful black Lab with a shiny coat and bright eyes. She's very intelligent and knows several tricks. She would thrive in an active household.",
        "dog_birthday": "4/12/2022",
        "dog_weight": 48,
        "dog_color": "black"
    }
]

def get_api_url():
    """Get API URL from environment or use default"""
    return os.environ.get('API_URL', 'http://localhost:3001')

def create_dog(api_url, dog_data):
    """Create a dog via the API"""
    try:
        response = requests.post(f"{api_url}/dogs", json=dog_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating dog {dog_data['dog_name']}: {e}")
        return None

def vote_on_dog(api_url, dog_id, vote_type="wag"):
    """Vote on a dog"""
    try:
        vote_data = {
            "user_id": f"test-user-{random.randint(1, 100)}",
            "vote_type": vote_type
        }
        response = requests.post(f"{api_url}/dogs/{dog_id}/vote", json=vote_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error voting on dog {dog_id}: {e}")
        return None

def main():
    """Main function to populate test data"""
    print("🐕 Populating Pupper with test data...")
    print("=" * 50)
    
    api_url = get_api_url()
    print(f"API URL: {api_url}")
    
    # Test API connectivity
    try:
        response = requests.get(f"{api_url}/dogs", timeout=10)
        print(f"✅ API is accessible (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is deployed and running")
        return
    
    created_dogs = []
    
    # Create test dogs
    print("\n📝 Creating test dogs...")
    for i, dog_data in enumerate(TEST_DOGS, 1):
        print(f"Creating dog {i}/{len(TEST_DOGS)}: {dog_data['dog_name']}")
        
        result = create_dog(api_url, dog_data)
        if result and result.get('success'):
            dog_id = result['data']['dog_id']
            created_dogs.append(dog_id)
            print(f"  ✅ Created {dog_data['dog_name']} (ID: {dog_id})")
        else:
            print(f"  ❌ Failed to create {dog_data['dog_name']}")
    
    print(f"\n✅ Successfully created {len(created_dogs)} dogs")
    
    # Add some votes to make it more realistic
    print("\n🗳️  Adding random votes...")
    for dog_id in created_dogs:
        # Add random number of wags (1-15)
        wag_count = random.randint(1, 15)
        for _ in range(wag_count):
            vote_on_dog(api_url, dog_id, "wag")
        
        # Add random number of growls (0-3)
        growl_count = random.randint(0, 3)
        for _ in range(growl_count):
            vote_on_dog(api_url, dog_id, "growl")
        
        print(f"  Added {wag_count} wags and {growl_count} growls to dog {dog_id}")
    
    print("\n🎉 Test data population complete!")
    print(f"Visit your frontend application to see {len(created_dogs)} adorable Labradors!")
    
    # Display summary
    print("\n📊 Summary:")
    print(f"  - Dogs created: {len(created_dogs)}")
    print(f"  - States represented: {len(set(dog['state'] for dog in TEST_DOGS))}")
    print(f"  - Shelters: {len(set(dog['shelter_name'] for dog in TEST_DOGS))}")
    print(f"  - Colors: {len(set(dog['dog_color'] for dog in TEST_DOGS))}")

if __name__ == "__main__":
    main()
