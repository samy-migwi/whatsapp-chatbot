import re
import datetime
from .handler import send_reply, handle_menu, handle_balance_options, handle_tag_options, user_states, reset_user_state
from database.models import log_message, add_pending_action
from database.queries import fetch_balance_by_phone, fetch_balance_by_phone_and_id, verify_parent, fetch_children_by_parent_phone,deactivate_child_tag

def process_message(data):
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages_data = value.get("messages", [])
        
        for msg in messages_data:
            sender = msg["from"]
            text = msg.get("text", {}).get("body", "[non-text message]")
            
            log_message(sender, text, "Processing", success=True)
            
            if msg.get("type") == "interactive" and msg["interactive"]["type"] == "button_reply":
                button_id = msg["interactive"]["button_reply"]["id"]
                reply = handle_button_response(sender, button_id)
            else:
                reply = generate_reply(sender, text)
            
            if reply:
                send_reply(sender, reply)
                
    except Exception as e:
        print(f"⚠️ Error processing message: {e}")

def handle_button_response(sender, button_id):
    # Handle child selection buttons (if you still want to support both)
    if button_id.startswith("child_"):
        return handle_tag_report_flow(sender, button_id)
    
    button_handlers = {
        "option_1": lambda: send_balance_options(sender),
        "option_2": lambda: handle_tag_report_flow(sender, "start"),
        "option_3": lambda: fetch_children_by_parent_phone(sender),
        "option_4": lambda: send_topup_instructions(sender),
        "option_5": lambda: start_phone_change(sender),
        "option_6": lambda: connect_to_support(sender),
        "balance_own": lambda: fetch_balance_by_phone(sender),
        "balance_other": lambda: request_other_balance_phone(sender),
        "tag_replace": lambda: handle_tag_action_response(sender, "tag_replace"),
        "tag_wait": lambda: handle_tag_action_response(sender, "tag_wait"),
        "menu_back": lambda: send_main_menu(sender)
    }
    
    handler = button_handlers.get(button_id)
    if handler:
        result = handler()
        return result if result is not None else ""
    else:
        return "❓ I didn't understand that selection. Please try again."

def send_balance_options(sender):
    menu_text, buttons = handle_balance_options()
    send_reply(sender, menu_text, buttons)
    return ""

def send_tag_options(sender):
    menu_text, buttons = handle_tag_options()
    send_reply(sender, menu_text, buttons)
    return ""

def send_topup_instructions(sender):
    response = (
        "💳 *Top-Up Instructions via M-PESA*\n\n"
        "📱 Go to *Lipa na M-Pesa*\n"
        "🏦 Select *Paybill*\n\n"
        "🔢 *Business Number*: 956781\n"
        "👤 *Account*: Your registered phone number\n"
        "💰 *Amount*: Enter desired amount\n"
        "🔐 *PIN*: Enter your M-PESA PIN\n\n"
        "✅ Confirmation will follow."
    )
    send_reply(sender, response)
    return ""

def start_phone_change(sender):
    user_states[sender] = "awaiting_phone_change_type"
    response = (
        "📞 *Phone Number Update*\n\n"
        "Is this change for:\n"
        "• Your own number\n"
        "• Another parent's number\n\n"
        "Please reply with:\n"
        "SELF → For your own number\n"
        "OTHER → For another parent's number"
    )
    send_reply(sender, response)
    return ""

def connect_to_support(sender):
    response = "🧑‍💼 We'll connect you to a support agent shortly. Please wait..."
    send_reply(sender, response)
    return ""

def request_other_balance_phone(sender):
    user_states[sender] = "awaiting_balance_phone"
    response = "📞 Please enter the parent's phone number:\nFormat: 254712345678"
    send_reply(sender, response)
    return ""

def handle_tag_replacement(sender):
    response = (
        "📦 *Replacement initiated!*\n\n"
        "✅ A new tag will be issued.\n"
        "💸 *Fee*: Ksh 69\n"
        "⚠️ Ensure your account has enough funds.\n\n"
        "🙏 Thank you!"
    )
    send_reply(sender, response)
    return ""

def handle_tag_wait(sender):
    response = (
        "⏳ *Tag deactivated temporarily.*\n\n"
        "🕒 Monitoring for 3 days.\n"
        "📌 If not recovered, pay *Ksh 69* for a new tag."
    )
    send_reply(sender, response)
    return ""

def send_main_menu(sender):
    response = handle_menu()
    send_reply(sender, response)
    return ""

def check_balance(sender, incoming_text):
    current_state = user_states.get(sender)
    
    if current_state == "awaiting_balance_phone":
        phone = incoming_text.strip()
        if re.match(r'^2547\d{8}$', phone):
            user_states[sender] = "awaiting_balance_id"
            user_states[f"{sender}_balance_phone"] = phone
            return "✅ Phone number accepted. Now please enter the ID number:"
        else:
            return "⚠️ Invalid phone format. Please use format: 254712345678"
    
    elif current_state == "awaiting_balance_id":
        national_id = incoming_text.strip()
        if re.match(r'^\d{6,8}$', national_id):
            phone = user_states.get(f"{sender}_balance_phone")
            user_states[sender] = None
            if f"{sender}_balance_phone" in user_states:
                del user_states[f"{sender}_balance_phone"]
            return fetch_balance_by_phone_and_id(phone, national_id)
        else:
            return "⚠️ Invalid ID format. ID should be 6-8 digits."
    
    if incoming_text == "1":
        send_balance_options(sender)
        return ""
    elif incoming_text == "1.1":
        return fetch_balance_by_phone(sender)
    elif incoming_text == "1.2":
        request_other_balance_phone(sender)
        return ""
    
    return "❓ Invalid option for balance checking."

def log_phone_change_request(sender, old_phone, national_id, new_phone):
    details = {
        "old_phone": old_phone,
        "new_phone": new_phone,
        "national_id": national_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    add_pending_action("phone_change", sender, details)
    print(f"📋 Phone Change Request Logged for {sender}")

def generate_reply(sender, text):
    text_lower = text.strip().lower()
    
    # Debug print to see what's being processed
    print(f"DEBUG: Processing '{text}' from {sender}, text_lower: '{text_lower}'")
    print(f"DEBUG: Current state: {user_states.get(sender)}")
    
    if text_lower in ["menu", "start", "hi", "hello", "help"]:
        reset_user_state(sender)
        return handle_menu()
    
    current_state = user_states.get(sender)
    
    # Check current state FIRST before menu handlers
    if current_state in ["awaiting_balance_phone", "awaiting_balance_id"]:
        return check_balance(sender, text)
    
    if current_state == "awaiting_phone_change_type":
        if text_lower == "self":
            user_states[sender] = "awaiting_phone_verification"
            return (
                "🔐 *Phone Number Update (Your Own Number)*\n\n"
                "Please reply with your current registered phone number and National ID:\n"
                "`2547XXXXXXXX, 12345678`"
            )
        elif text_lower == "other":
            user_states[sender] = None
            return (
                "❌ For security reasons, changing another parent's phone number requires in-person verification.\n\n"
                "Please visit the school administration office to fill out the required registration form.\n\n"
                "🏫 School Hours: Mon-Fri, 8AM-4PM\n\n"
                + handle_menu()
            )
        else:
            return "⚠️ Please reply with SELF or OTHER"
    
    if current_state == "awaiting_phone_verification":
        try:
            parts = [x.strip() for x in text.split(",")]
            if len(parts) == 2:
                old_phone, id_input = parts
                if verify_parent(old_phone, id_input):
                    user_states[sender] = "awaiting_new_number"
                    user_states[f"{sender}_old_phone"] = old_phone
                    user_states[f"{sender}_id"] = id_input
                    return "✅ Verified. Now reply with your *new phone number*:\n`2547YYYYYYYY`"
                else:
                    reset_user_state(sender)
                    return "❌ No matching parent found. Please check your details."
            else:
                return "⚠️ Invalid format. Please send: `2547XXXXXXXX, 12345678`"
        except:
            return "⚠️ Invalid format. Please send: `2547XXXXXXXX, 12345678`"
    
    elif current_state == "awaiting_new_number":
        new_phone = text.strip()
        old_phone = user_states.get(f"{sender}_old_phone")
        id_input = user_states.get(f"{sender}_id")

        if old_phone and id_input:
            log_phone_change_request(sender, old_phone, id_input, new_phone)
            reset_user_state(sender)
            
            return (
                "📥 *Request Received!*\n\n"
                "Your phone number change request has been forwarded to our team.\n"
                "🔍 They will verify and update your account manually.\n"
                "⏳ Please allow up to 24 hours for processing.\n\n"
                "🙏 Thank you for your patience!"
            )
        else:
            reset_user_state(sender)
            return "❌ Error processing your request. Please start over."
    
    elif current_state == "awaiting_tag_action":
        if text_lower == "1":
            reset_user_state(sender)
            return handle_tag_replacement(sender)
        elif text_lower == "2":
            reset_user_state(sender)
            return handle_tag_wait(sender)
        elif text_lower == "back":
            # Go back to child selection
            user_states[sender] = "awaiting_child_selection"
            children = user_states.get(f"{sender}_children", [])
            menu_text = "👧 Which child lost their tag? Please reply with the number:\n\n"
            for i, child in enumerate(children, 1):
                child_id, full_name, gender, school_name, grade, tag_id, tag_status = child
                menu_text += f"{i}. {full_name} ({grade}) - {school_name}\n"
            menu_text += "\n🔙 Reply with 'back' to return to main menu"
            return menu_text
        else:
            return "❓ Reply with 1, 2, or 'back' to proceed."
    
    elif current_state == "awaiting_child_selection":
        # Handle child selection here
        if text_lower == "back":
            reset_user_state(sender)
            return handle_menu()
        
        try:
            selected_number = int(text)
            children = user_states.get(f"{sender}_children", [])
            
            if 1 <= selected_number <= len(children):
                selected_child = children[selected_number - 1]
                child_id, full_name, gender, school_name, grade, tag_id, tag_status = selected_child
                user_states[sender] = "awaiting_tag_action"
                user_states[f"{sender}_selected_child"] = selected_child
                
                # Show tag options
                menu_text = (
                    f"😔 Sorry to hear {full_name}'s tag is missing.\n\n"
                    "Please choose how to proceed:\n\n"
                    "1. 🔄 Replace Now (Ksh 69) - Immediate replacement\n"
                    "2. ⏳ Wait 3 Days (Free) - Monitor first\n\n"
                    "🔙 Reply with 'back' to choose different child"
                )
                
                return menu_text
            else:
                return "⚠️ Invalid number. Please select a number from the list."
                
        except ValueError:
            return "⚠️ Please reply with a number (1, 2, 3, etc.)"
    
    # ONLY AFTER checking all states, check menu handlers
    menu_handlers = {
        "1": lambda: send_balance_options(sender),
        "2": lambda: handle_tag_report_flow(sender, "start"),
        "3": lambda: fetch_children_by_parent_phone(sender),
        "4": lambda: send_topup_instructions(sender),
        "5": lambda: start_phone_change(sender),
        "6": lambda: connect_to_support(sender)
    }
    
    if text_lower in menu_handlers:
        print(f"DEBUG: Found menu handler for '{text_lower}'")
        result = menu_handlers[text_lower]()
        
        # Handle different return types
        if result is None:
            print("DEBUG: Handler returned None")
            return ""
            
        elif isinstance(result, tuple) and len(result) == 2:
            # Handler returned (menu_text, buttons) - send them and return empty string
            menu_text, buttons = result
            print(f"DEBUG: Sending buttons with text: {menu_text[:50]}...")
            send_reply(sender, menu_text, buttons)
            return ""
            
        else:
            # Handler returned a string - return it normally
            print(f"DEBUG: Handler returned string: {result[:50]}...")
            return result
    
    elif text_lower in ["1.1", "1.2"]:
        return check_balance(sender, text_lower)
    
    else:
        print(f"DEBUG: No handler found for '{text_lower}', showing default error")
        return "❌ We were not able to process that. Please use the menu options below:\n\n" + handle_menu()

def handle_tag_action_response(sender, action):
    """Handle tag action responses (replace/wait)"""
    selected_child = user_states.get(f"{sender}_selected_child")
    if not selected_child:
        reset_user_state(sender)
        return "❌ Session expired. Please start over."
    
    child_id, full_name, gender, school_name, grade, tag_id, tag_status = selected_child
    
    if action == "tag_replace":
        # Deactivate tag and create pending action
        if deactivate_child_tag(child_id):
            details = {
                "child_id": child_id,
                "child_name": full_name,
                "grade": grade,
                "original_tag_id": tag_id,
                "option_chosen": "replace_now",
                "fee_required": True,
                "fee_amount": 69.00
            }
            add_pending_action("tag_replacement", sender, details)
            
            reset_user_state(sender)
            return "✅ Tag deactivated! Replacement request submitted. Ksh 69 will be processed. Admin will assign a new tag shortly."
    
    elif action == "tag_wait":
        # Deactivate tag and create monitoring action
        if deactivate_child_tag(child_id):
            details = {
                "child_id": child_id,
                "child_name": full_name,
                "grade": grade,
                "original_tag_id": tag_id,
                "option_chosen": "wait_3_days",
                "fee_required": False
            }
            add_pending_action("tag_replacement", sender, details)
            
            reset_user_state(sender)
            return "⏳ Tag deactivated! We'll monitor for 3 days. If not found, replacement will be initiated automatically."
    
    return "❌ Error processing your request. Please try again."

def handle_tag_report_flow(sender, text):
    """Handle the complete tag reporting flow using numbered list"""
    current_state = user_states.get(sender)
    
    # Step 1: Show children with active tags as numbered list
    if current_state is None or text == "start":
        # Use the enhanced function to get children with tag info
        children_with_tags = fetch_children_by_parent_phone(sender, include_tags=True)
        
        if not children_with_tags:
            return "❌ No children with active tags found for your account."
        
        # Filter only children with active tags
        children_with_active_tags = [child for child in children_with_tags if child[6] == 'active']
        
        if not children_with_active_tags:
            return "❌ No active tags found for your children."
        
        user_states[sender] = "awaiting_child_selection"
        user_states[f"{sender}_children"] = children_with_active_tags
        
        # Create numbered list instead of buttons
        menu_text = "👧 Which child lost their tag? Please reply with the number:\n\n"
        for i, child in enumerate(children_with_active_tags, 1):
            child_id, full_name, gender, school_name, grade, tag_id, tag_status = child
            menu_text += f"{i}. {full_name} ({grade}) - {school_name}\n"
        
        menu_text += "\n🔙 Reply with 'back' to return to main menu"
        
        return menu_text  # Return simple text instead of buttons
    
    # Step 2: Handle child selection by number
    elif current_state == "awaiting_child_selection":
        if text.lower() == "back":
            reset_user_state(sender)
            return handle_menu()
        
        try:
            selected_number = int(text)
            children = user_states.get(f"{sender}_children", [])
            
            if 1 <= selected_number <= len(children):
                selected_child = children[selected_number - 1]
                child_id, full_name, gender, school_name, grade, tag_id, tag_status = selected_child
                user_states[sender] = "awaiting_tag_action"
                user_states[f"{sender}_selected_child"] = selected_child
                
                # Show tag options as numbered list
                menu_text = (
                    f"😔 Sorry to hear {full_name}'s tag is missing.\n\n"
                    "Please choose how to proceed:\n\n"
                    "1. 🔄 Replace Now (Ksh 69) - Immediate replacement\n"
                    "2. ⏳ Wait 3 Days (Free) - Monitor first\n\n"
                    "🔙 Reply with 'back' to choose different child"
                )
                
                return menu_text  # Return simple text instead of buttons
            else:
                return "⚠️ Invalid number. Please select a number from the list."
                
        except ValueError:
            return "⚠️ Please reply with a number (1, 2, 3, etc.)"
    
    # Step 3: Handle tag action selection
    elif current_state == "awaiting_tag_action":
        if text.lower() == "back":
            user_states[sender] = "awaiting_child_selection"
            # Re-show children list
            children = user_states.get(f"{sender}_children", [])
            menu_text = "👧 Which child lost their tag? Please reply with the number:\n\n"
            for i, child in enumerate(children, 1):
                child_id, full_name, gender, school_name, grade, tag_id, tag_status = child
                menu_text += f"{i}. {full_name} ({grade}) - {school_name}\n"
            menu_text += "\n🔙 Reply with 'back' to return to main menu"
            return menu_text
        
        selected_child = user_states.get(f"{sender}_selected_child")
        if not selected_child:
            reset_user_state(sender)
            return "❌ Session expired. Please start over."
        
        child_id, full_name, gender, school_name, grade, tag_id, tag_status = selected_child
        
        if text == "1":
            # Deactivate tag and create pending action for replacement
            if deactivate_child_tag(child_id):
                details = {
                    "child_id": child_id,
                    "child_name": full_name,
                    "grade": grade,
                    "original_tag_id": tag_id,
                    "option_chosen": "replace_now",
                    "fee_required": True,
                    "fee_amount": 69.00
                }
                add_pending_action("tag_replacement", sender, details)
                
                reset_user_state(sender)
                return "✅ Tag deactivated! Replacement request submitted. Ksh 69 will be processed. Admin will assign a new tag shortly."
        
        elif text == "2":
            # Deactivate tag and create monitoring action
            if deactivate_child_tag(child_id):
                details = {
                    "child_id": child_id,
                    "child_name": full_name,
                    "grade": grade,
                    "original_tag_id": tag_id,
                    "option_chosen": "wait_3_days",
                    "fee_required": False
                }
                add_pending_action("tag_replacement", sender, details)
                
                reset_user_state(sender)
                return "⏳ Tag deactivated! We'll monitor for 3 days. If not found, replacement will be initiated automatically."
        
        else:
            return "⚠️ Please reply with 1 or 2 to proceed."
    
    return ""
 
def handle_children_list(sender, children):
    """NEW - Shows list of children for selection"""
    menu_text = "👧 Which child lost their tag?\n\n"
    
    buttons = []
    for i, child in enumerate(children, 1):
        child_id, full_name, gender, school_name, grade, tag_id, tag_status = child
        buttons.append({
            "type": "reply",
            "reply": {
                "id": f"child_{child_id}",
                "title": f"👤 {full_name} ({grade})"
            }
        })
    
    buttons.append({
        "type": "reply",
        "reply": {
            "id": "menu_back",
            "title": "🔙 Back to Menu"
        }
    })
    
    return menu_text, buttons

def handle_tag_options_with_children(sender, children):
    """NEW - Shows tag options for a specific child"""
    child_id, full_name, gender, school_name, grade, tag_id, tag_status = children[0]
    
    menu_text = f"😔 Sorry to hear {full_name}'s tag is missing.\n\nPlease choose how to proceed:"
    
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": "tag_replace",
                "title": "🔄 Replace Now (Ksh 69)"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "tag_wait",
                "title": "⏳ Wait 3 Days (Free)"
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