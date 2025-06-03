from flask import Flask, request, jsonify, session, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_cors import CORS # Import CORS
import json
import subprocess

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY']
)

# Adjust static_folder path for local development (relative to app.py)
app = Flask(__name__, static_folder='frontend/build', static_url_path='/')

# Configure CORS to allow requests from your React development server (localhost:3000)
# In production, specify your React app's actual domain(s) for security.
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Generate a random secret key for session management.
# In a production environment, this should be loaded from an environment variable or a secure configuration.
app.secret_key = os.urandom(24)

# In-memory user and chat history storage (use database in production)
users = {'admin': 'adminpass'}
chat_histories = {} # Stores chat history for each user: {'username': [{'role': 'user', 'content': 'prompt'}, {'role': 'assistant', 'content': 'reply'}], ...}

# This route will serve the React app's built index.html
# In local development, you'll run React separately, so this is mostly for production serving.
@app.route('/')
def serve_react_app():
    # This route will only be hit if you access Flask directly without React's dev server.
    # During React dev, you'll access http://localhost:3000 directly.
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if username in users and users[username] == password:
        session['username'] = username
        if username not in chat_histories:
            chat_histories[username] = []
        return jsonify({"message": "Login successful", "username": username}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if username in users:
        return jsonify({"message": "Username already exists."}), 409
    else:
        users[username] = password
        chat_histories[username] = []
        return jsonify({"message": "Registration successful! You can now login."}), 201

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized. Please log in."}), 401

    username = session['username']
    data = request.get_json()
    prompt_text = data.get('prompt')

    if not prompt_text:
        return jsonify({"message": "Prompt cannot be empty."}), 400

    current_chat_history_for_openai = []
    for p, r in chat_histories.get(username, []):
        current_chat_history_for_openai.append({"role": "user", "content": p})
        current_chat_history_for_openai.append({"role": "assistant", "content": r})

    messages_for_openai = current_chat_history_for_openai + [{"role": "user", "content": prompt_text}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_openai
        )
        reply = response.choices[0].message.content

        chat_histories[username].append((prompt_text, reply))
        return jsonify({"reply": reply, "history": chat_histories[username]}), 200

    except Exception as e:
        error_message = f"Error communicating with the chatbot: {e}. Please check your API key and internet connection."
        chat_histories[username].append((prompt_text, error_message))
        return jsonify({"reply": error_message, "history": chat_histories[username]}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized. Please log in."}), 401

    username = session['username']
    history = chat_histories.get(username, [])
    return jsonify({"history": history}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    if 'username' in session:
        return jsonify({"isAuthenticated": True, "username": session['username']}), 200
    return jsonify({"isAuthenticated": False}), 200

if __name__ == "__main__":
    # Ensure Flask runs on port 5000 as React expects to proxy to it
    app.run(host='0.0.0.0', port=5000, debug=True)