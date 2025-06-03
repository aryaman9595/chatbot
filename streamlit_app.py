import streamlit as st
import requests
import json

# Configure the base URL for the Flask backend
FLASK_API_BASE_URL = "http://localhost:5000/api"

def init_session_state():
    """Initialize session state variables if they don't exist"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def login(username, password):
    """Attempt to log in user"""
    try:
        response = requests.post(
            f"{FLASK_API_BASE_URL}/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.username = data['username']
            st.success("Login successful!")
            return True
        else:
            st.error(response.json().get('message', 'Login failed'))
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def register(username, password):
    """Register a new user"""
    try:
        response = requests.post(
            f"{FLASK_API_BASE_URL}/register",
            json={"username": username, "password": password}
        )
        if response.status_code == 201:
            st.success("Registration successful! You can now login.")
            return True
        else:
            st.error(response.json().get('message', 'Registration failed'))
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def send_message(prompt):
    """Send a message to the chatbot"""
    try:
        response = requests.post(
            f"{FLASK_API_BASE_URL}/chat",
            json={"prompt": prompt}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.chat_history = data['history']
            return True
        else:
            st.error(response.json().get('message', 'Failed to send message'))
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def logout():
    """Log out the current user"""
    try:
        response = requests.post(f"{FLASK_API_BASE_URL}/logout")
        if response.status_code == 200:
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.chat_history = []
            st.success("Logged out successfully!")
            return True
        else:
            st.error("Failed to logout")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def main():
    st.title("AI Chatbot")
    init_session_state()

    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                login(username, password)

        with tab2:
            st.header("Register")
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            if st.button("Register"):
                register(username, password)

    else:
        st.sidebar.write(f"Logged in as: {st.session_state.username}")
        if st.sidebar.button("Logout"):
            logout()

        # Chat interface
        st.subheader("Chat")
        
        # Display chat history
        for prompt, response in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                st.write(response)

        # Chat input
        prompt = st.chat_input("Type your message here...")
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)
            
            if send_message(prompt):
                # Get the last response from the chat history
                if st.session_state.chat_history:
                    with st.chat_message("assistant"):
                        st.write(st.session_state.chat_history[-1][1])

if __name__ == "__main__":
    main()

