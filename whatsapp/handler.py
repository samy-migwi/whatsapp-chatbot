import requests
from config import WHATSAPP_CONFIG
from database.models import log_message

user_states = {}

def send_reply(sender, reply, buttons=None):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_CONFIG['phone_number_id']}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_CONFIG['access_token']}",
        "Content-Type": "application/json"
    }
    
    if buttons and len(buttons) <= 3:
        payload = {
            "messaging_product": "whatsapp",
            "to": sender,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": reply
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": sender,
            "type": "text",
            "text": {"body": reply}
        }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("✅ Reply sent successfully to", sender)
        log_message(sender, "Outgoing", reply, success=True)
        return True
    except requests.exceptions.RequestException as e:
        print("❌ Error sending reply:", e)
        log_message(sender, "Outgoing", f"Failed to send: {str(e)}", success=False)
        return False

def handle_menu():
    return (
        "Welcome to School Parent Portal! 🎒\n\n"
        "1️⃣ Check Balance → Reply with: *1*\n"
        "2️⃣ Report Lost Tag → Reply with: *2*\n"
        "3️⃣ View Children → Reply with: *3*\n"
        "4️⃣ Top-Up Instructions → Reply with: *4*\n"
        "5️⃣ Change Phone Number → Reply with: *5*\n"
        "6️⃣ Talk to Support → Reply with: *6*\n"
        "🧑‍💼 We'll connect you to someone who can assist."
    )


def handle_balance_options():
    menu_text = "💰 View your current account balance or someone else's.\n\nPlease select:"
    
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": "balance_own",
                "title": "👤 My Balance"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "balance_other",
                "title": "👥 Other Parent"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "menu_back",
                "title": "🔙 Back to Menu"
            }
        }
    ]
    
    return menu_text, buttons

def handle_tag_options():
    menu_text = "😔 Sorry to hear the tag is missing.\n\nPlease choose how to proceed:"
    
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": "tag_replace",
                "title": "🔄 Replace Now"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "tag_wait",
                "title": "⏳ Wait 3 Days"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "menu_back",
                "title": "🔙 Back to Menu"
            }
        }
    ]
    
    return menu_text, buttons

def reset_user_state(sender):
    if sender in user_states:
        del user_states[sender]
    for key in list(user_states.keys()):
        if key.startswith(f"{sender}_"):
            del user_states[key]