import os
import json
import tweepy

# Load environment variables from local.settings.json
with open('../AzureFunctions/local.settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)
    for key, value in settings['Values'].items():
        os.environ[key] = value

def test_auth(bot_name, prefix):
    """Test Twitter authentication for a bot"""
    print(f"\n=== Testing {bot_name} Authentication ===")

    try:
        client = tweepy.Client(
            consumer_key=os.environ[f'{prefix}_CONSUMER_KEY'],
            consumer_secret=os.environ[f'{prefix}_CONSUMER_SECRET'],
            access_token=os.environ[f'{prefix}_ACCESS_TOKEN'],
            access_token_secret=os.environ[f'{prefix}_ACCESS_TOKEN_SECRET']
        )

        # Get authenticated user info (read-only operation)
        me = client.get_me()

        if me.data:
            print(f"✅ Authentication successful!")
            print(f"   Username: @{me.data.username}")
            print(f"   Name: {me.data.name}")
            print(f"   ID: {me.data.id}")
        else:
            print("❌ Authentication failed: No user data returned")

    except Exception as e:
        print(f"❌ Authentication failed: {e}")

test_auth("TehilimBot", "TEHILIM")
test_auth("GilgameshBot", "GILGAMESH")
