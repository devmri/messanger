import json
import logging
from datetime import datetime
from config import ACCESS_TOKEN, GROUP_ID
import requests

BAN_FILE = 'ban_list.json'

def load_ban_list():
    try:
        with open(BAN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ban_list(ban_list):
    with open(BAN_FILE, 'w') as f:
        json.dump(ban_list, f, indent=4)

def remove_expired_bans(ban_list):
    now = datetime.now()
    for user_id, ban_info in list(ban_list.items()):
        if datetime.fromisoformat(ban_info['ban_until']) <= now:
            del ban_list[user_id]
    save_ban_list(ban_list)

def send_message(user_id, text):
    url = 'https://graph.facebook.com/v12.0/me/messages'
    headers = {'Content-Type': 'application/json'}
    data = {
        'recipient': {'id': user_id},
        'message': {'text': text},
        'access_token': ACCESS_TOKEN
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Failed to send message: {str(e)}")
        return False

def send_welcome_message(user_id, user_name):
    welcome_message = (
        f"🌟 Welcome to our group / গ্রুপে স্বাগতম 🌟\n\n"
        f"Dear @{user_name},\n"
        f"Welcome to our community! Please read and follow our group rules.\n\n"
        f"প্রিয় @{user_name},\n"
        f"আমাদের কমিউনিটিতে স্বাগতম! অনুগ্রহ করে গ্রুপের নিয়মাবলী পড়ুন এবং মেনে চলুন।"
    )
    return send_message(user_id, welcome_message)

def remove_user_from_group(user_id):
    url = f'https://graph.facebook.com/{GROUP_ID}/members'
    data = {
        'member': user_id,
        'access_token': ACCESS_TOKEN
    }
    try:
        response = requests.delete(url, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Failed to remove user: {str(e)}")
        return False