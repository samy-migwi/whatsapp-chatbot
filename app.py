from flask import Flask, request, Response, jsonify, render_template
from config import Config
from database.models import init_database, get_recent_messages, get_dashboard_metrics, get_pending_actions
from whatsapp.message_processor import process_message

app = Flask(__name__)
app.config.from_object(Config)

init_database()

@app.route('/')
def dashboard():
    metrics = get_dashboard_metrics()
    messages = get_recent_messages(50)
    pending_actions = get_pending_actions()
    
    return render_template('dashboard.html', 
                         metrics=metrics, 
                         messages=messages, 
                         pending_actions=pending_actions)

@app.route('/api/metrics')
def api_metrics():
    metrics = get_dashboard_metrics()
    return jsonify(metrics)

@app.route('/api/messages')
def api_messages():
    limit = request.args.get('limit', 50, type=int)
    messages = get_recent_messages(limit)
    
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            'id': msg[0],
            'sender': msg[1],
            'message': msg[2],
            'response': msg[3],
            'success': msg[4],
            'error_message': msg[5],
            'timestamp': msg[6].strftime('%Y-%m-%d %H:%M:%S') if msg[6] else None
        })
    
    return jsonify(formatted_messages)

@app.route('/api/pending-actions')
def api_pending_actions():
    actions = get_pending_actions()
    
    formatted_actions = []
    for action in actions:
        formatted_actions.append({
            'id': action[0],
            'action_type': action[1],
            'sender': action[2],
            'details': action[3],
            'created_at': action[4].strftime('%Y-%m-%d %H:%M:%S') if action[4] else None
        })
    
    return jsonify(formatted_actions)

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == Config.WEBHOOK_VERIFY_TOKEN:
        return Response(challenge, status=200, mimetype='text/plain')
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        process_message(data)
        return "OK", 200
    except Exception as e:
        print("⚠️ Error processing message:", e)
        return "Error processing message", 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )