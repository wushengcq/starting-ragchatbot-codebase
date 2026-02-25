#!/usr/bin/env python3
"""
Test script to validate BigModel (ZhipuAI) API key.
Run this script to check if your API key is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_key():
    """Test the BigModel API key"""

    print("=" * 60)
    print("BigModel (ZhipuAI) API Key Test")
    print("=" * 60)

    # Get API key
    api_key = os.getenv("BIGMODEL_API_KEY")

    # Check 1: API key exists
    if not api_key:
        print("\n❌ FAIL: BIGMODEL_API_KEY not found in .env file")
        print("\nPlease add your API key to the .env file:")
        print("BIGMODEL_API_KEY=your.api.key.here")
        return False

    print(f"\n✅ API key found in .env file")
    print(f"   Key length: {len(api_key)} characters")

    # Check 2: API key format
    if "." not in api_key or len(api_key) < 20:
        print(f"\n⚠️  WARNING: API key format looks incorrect")
        print(f"   Expected format: id.secret (e.g., 12345678.abcd1234...)")
        print(f"   Your key: {api_key[:10]}...{api_key[-10:]}")
    else:
        parts = api_key.split(".")
        print(f"\n✅ API key format looks correct (id.secret)")
        print(f"   ID: {parts[0]}")
        print(f"   Secret: {parts[1][:10]}...{parts[1][-10:]}")

    # Check 3: Test API connection
    print(f"\n🔄 Testing API connection...")

    try:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=api_key)

        # Make a simple test call
        response = client.chat.completions.create(
            model="glm-5",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful' in English."}
            ],
            max_tokens=50
        )

        # Check if we got a valid response
        if response and response.choices:
            result = response.choices[0].message.content
            print(f"✅ API connection successful!")
            print(f"   Response: {result}")
            print(f"\n{'=' * 60}")
            print("✅ Your API key is working correctly!")
            print("=" * 60)
            return True
        else:
            print(f"❌ FAIL: API returned unexpected response")
            return False

    except ImportError as e:
        print(f"❌ FAIL: Cannot import zhipuai library")
        print(f"   Error: {e}")
        print(f"\n💡 Solution: Run 'uv sync' to install dependencies")
        return False

    except Exception as e:
        error_str = str(e)

        if "401" in error_str or "1000" in error_str or "身份验证" in error_str:
            print(f"\n❌ FAIL: API authentication failed (401)")
            print(f"   Error: {e}")
            print(f"\n💡 Possible solutions:")
            print(f"   1. Your API key is incorrect or expired")
            print(f"   2. Get a new API key from: https://open.bigmodel.cn/")
            print(f"   3. Make sure you're using the correct key (not a test key)")
            print(f"   4. Check if the key has sufficient credits/quota")
        else:
            print(f"\n❌ FAIL: API request failed")
            print(f"   Error: {e}")
            print(f"\n💡 Check:")
            print(f"   1. Your internet connection")
            print(f"   2. API service status at https://open.bigmodel.cn/")
            print(f"   3. Your API key quota/credits")

        return False


if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)
