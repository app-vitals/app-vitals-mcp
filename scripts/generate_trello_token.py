#!/usr/bin/env python3
"""
Script to help generate Trello API tokens.

This script will:
1. Read your API key from environment or prompt for it
2. Open your browser to the Trello authorization page
3. Guide you through copying the token
4. Optionally save it to your .env file
"""

import os
import sys
import webbrowser
from pathlib import Path
from dotenv import load_dotenv, set_key


def get_api_key():
    """Get API key from environment or user input."""
    load_dotenv()
    api_key = os.getenv("TRELLO_API_KEY")
    
    if api_key:
        print(f"Found API key in environment: {api_key[:8]}...")
        use_existing = input("Use this API key? (y/n): ").lower().strip()
        if use_existing == 'y':
            return api_key
    
    print("\nTo get your API key:")
    print("1. Go to https://trello.com/power-ups/admin")
    print("2. Create a new Power-Up or select an existing one")
    print("3. Copy the API Key (not the secret!)")
    print()
    
    api_key = input("Enter your Trello API key: ").strip()
    if not api_key:
        print("API key is required!")
        sys.exit(1)
    
    return api_key


def generate_auth_url(api_key):
    """Generate the authorization URL."""
    base_url = "https://trello.com/1/authorize"
    params = {
        "expiration": "never",
        "scope": "read,write",
        "response_type": "token",
        "key": api_key,
        "name": "Trello MCP Server"
    }
    
    url = f"{base_url}?" + "&".join(f"{k}={v}" for k, v in params.items())
    return url


def save_to_env(api_key, token):
    """Save credentials to .env file."""
    env_path = Path(".env")
    
    # Update or create .env file
    set_key(env_path, "TRELLO_API_KEY", api_key)
    set_key(env_path, "TRELLO_TOKEN", token)
    
    print(f"\n✅ Credentials saved to {env_path.absolute()}")


def main():
    print("🔑 Trello Token Generator")
    print("=" * 30)
    
    # Get API key
    api_key = get_api_key()
    
    # Generate authorization URL
    auth_url = generate_auth_url(api_key)
    
    print(f"\n🌐 Opening authorization page...")
    print(f"URL: {auth_url}")
    
    # Open browser
    try:
        webbrowser.open(auth_url)
        print("\n✅ Browser opened. If it didn't open automatically, copy the URL above.")
    except Exception as e:
        print(f"\n❌ Could not open browser: {e}")
        print(f"Please manually visit: {auth_url}")
    
    print("\n📋 Instructions:")
    print("1. Click 'Allow' on the Trello authorization page")
    print("2. Copy the token from the page (it will be a long string)")
    print("3. Paste it below")
    print()
    
    # Get token from user
    token = input("Enter the generated token: ").strip()
    if not token:
        print("Token is required!")
        sys.exit(1)
    
    # Validate token format (basic check)
    if len(token) < 50:
        print("⚠️  Warning: Token seems short. Make sure you copied the full token.")
    
    # Save to .env file
    save_env = input("\n💾 Save credentials to .env file? (y/n): ").lower().strip()
    if save_env == 'y':
        save_to_env(api_key, token)
    else:
        print("\n📝 Add these to your environment:")
        print(f"export TRELLO_API_KEY='{api_key}'")
        print(f"export TRELLO_TOKEN='{token}'")
    
    print("\n🎉 Done! You can now use the Trello MCP server.")
    print("\nTest your credentials with:")
    print("uv run pytest tests/servers/trello/test_integration.py -v -m integration")


if __name__ == "__main__":
    main()