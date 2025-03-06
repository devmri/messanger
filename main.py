from flask import Flask, request
from utils import send_message, load_ban_list, save_ban_list, remove_expired_bans, remove_user_from_group, send_welcome_message
from datetime import datetime, timedelta
import json
import logging
import os  # Add this import

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log'
)

app = Flask(__name__)
ban_list = load_ban_list()
remove_expired_bans(ban_list)

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logging.info(f"Webhook verification - Mode: {mode}, Token: {token}, Challenge: {challenge}")
    logging.info(f"Expected token: {os.getenv('FB_VERIFY_TOKEN')}")

    # Check if all required parameters are present
    if not all([mode, token, challenge]):
        logging.error("Missing required parameters")
        return 'Missing parameters', 400

    # Verify the token
    if token != os.getenv('FB_VERIFY_TOKEN'):
        logging.error("Token mismatch")
        return 'Invalid token', 403

    # Verify the mode
    if mode != 'subscribe':
        logging.error("Invalid mode")
        return 'Invalid mode', 403

    # All checks passed, return the challenge
    logging.info("Verification successful")
    return challenge

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if data and data.get('object') == 'page':
            for entry in data['entry']:
                # Handle messages
                if 'messaging' in entry:
                    for messaging in entry['messaging']:
                        if 'message' in messaging:
                            handle_message(messaging)

                # Handle new member added events
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'members' and change.get('value', {}).get('added_members'):
                            for new_member in change['value']['added_members']:
                                user_id = new_member.get('id')
                                user_name = new_member.get('name', 'New Member')
                                if user_id:
                                    send_welcome_message(user_id, user_name)

        return 'EVENT_RECEIVED', 200
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return 'ERROR', 500

def handle_message(messaging):
    user_id = messaging['sender']['id']
    user_name = messaging['sender'].get('name', 'User')

    if user_id in ban_list:
        return

    message_text = messaging['message'].get('text', '').lower()
    bad_words = ["bokacondon", "badword1", "badword2"]  # Add your bad words here

    if any(word in message_text for word in bad_words):
        violations = ban_list.get(user_id, {}).get('violations', 0) + 1
        if violations == 1:
            warning_message = (f"⚠️ Warning / সতর্কবার্তা ⚠️\n@{user_name}, you have used inappropriate language. "
                              f"Please follow the group rules.\n@{user_name}, আপনি অনুপযুক্ত ভাষা ব্যবহার করেছেন। "
                              "অনুগ্রহ করে গ্রুপের নিয়ম মেনে চলুন।")
            send_message(user_id, warning_message)
        elif violations == 2:
            ban_until = datetime.now() + timedelta(days=3)
            ban_list[user_id] = {
                'user_name': user_name,
                'ban_until': ban_until.isoformat(),
                'violations': violations
            }
            save_ban_list(ban_list)
            ban_message = (f"🚫 Temporary Ban / সাময়িক নিষেধাজ্ঞা 🚫\n@{user_name}, you are banned for 3 days due "
                           f"to repeated violations.\n@{user_name}, বারবার নিয়ম ভাঙার কারণে আপনাকে ৩ দিনের জন্য নিষিদ্ধ করা হয়েছে।")
            send_message(user_id, ban_message)
        elif violations >= 3:
            kick_message = (f"❌ Removed from Group / গ্রুপ থেকে সরানো হয়েছে ❌\n@{user_name}, you have been removed "
                            f"from the group due to repeated rule violations.\n@{user_name}, বারবার নিয়ম ভাঙার কারণে আপনাকে গ্রুপ থেকে সরানো হয়েছে।")
            send_message(user_id, kick_message)
            remove_user_from_group(user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)