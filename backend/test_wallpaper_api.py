#!/usr/bin/env python3
"""
Test script for wallpaper generation API
"""
import asyncio
import requests
import json

API_BASE = "http://localhost:8001/api"

def test_wallpaper_generation():
    """Test the wallpaper generation endpoint"""
    print("🧪 Testing wallpaper generation API...")

    # Test data
    test_prompts = [
        {
            "prompt": "Sunset over mountains with purple clouds",
            "style": "nature",
            "quality": "high"
        },
        {
            "prompt": "Abstract geometric patterns in blue and gold",
            "style": "abstract",
            "quality": "high"
        },
        {
            "prompt": "Minimalist mountain landscape",
            "style": "minimal",
            "quality": "high"
        }
    ]

    for i, test_data in enumerate(test_prompts, 1):
        print(f"\n📱 Test {i}: {test_data['prompt'][:50]}...")

        try:
            response = requests.post(
                f"{API_BASE}/wallpaper/generate",
                json=test_data,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ SUCCESS: Generated wallpaper")
                    print(f"   URL: {data.get('wallpaper_url')}")
                    print(f"   Style: {data.get('style')}")
                    print(f"   Aspect Ratio: {data.get('aspect_ratio')}")
                else:
                    print(f"❌ API ERROR: {data.get('error')}")
            else:
                print(f"❌ HTTP ERROR: {response.status_code}")
                print(f"   Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ REQUEST ERROR: {e}")

    print("\n🧪 Testing wallpaper history API...")
    try:
        response = requests.get(f"{API_BASE}/wallpaper/history", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                wallpapers = data.get("wallpapers", [])
                print(f"✅ SUCCESS: Retrieved {len(wallpapers)} wallpapers from history")
            else:
                print(f"❌ API ERROR: {data.get('error')}")
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")

def test_basic_api():
    """Test basic API connectivity"""
    print("🔌 Testing basic API connectivity...")

    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running: {data.get('message')}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting wallpaper API tests...\n")

    # Test basic connectivity first
    if test_basic_api():
        print()
        test_wallpaper_generation()
    else:
        print("❌ Cannot proceed with tests - API is not accessible")

    print("\n✨ Tests completed!")