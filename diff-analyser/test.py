#!/usr/bin/env python3
"""Test service configuration."""

from app.config import settings
from app.github_client import GitHubClient

def test_service_config():
    """Test if service can access GitHub with configured token."""
    
    print(f"🔍 Testing service configuration...")
    print(f"GitHub Token (first 10 chars): {settings.GITHUB_TOKEN[:10]}...")
    
    # Test GitHub client
    client = GitHubClient()
    
    try:
        # Test the exact same API call that's failing
        pr_details = client.get_pr_details("pooshans/assignment", 1)
        print("✅ GitHub API access successful!")
        print(f"PR Title: {pr_details['title']}")
        print(f"PR Author: {pr_details['user']['login']}")
        return True
        
    except Exception as e:
        print(f"❌ GitHub API access failed: {e}")
        return False

if __name__ == "__main__":
    test_service_config()
