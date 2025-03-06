import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Facebook API credentials
ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN', '')
GROUP_ID = os.getenv('FB_GROUP_ID', '')
VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN', '')

# Validation
if not all([ACCESS_TOKEN, GROUP_ID, VERIFY_TOKEN]):
    raise ValueError("Missing required environment variables. Please check your .env file.")