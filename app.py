import streamlit as st
import requests
import json
import mysql.connector

st.title("Flowe to Chat Bastion")
st.write("Start a conversation and delete the conversation at any time to start fresh.")

# Connect to the database
cnx = mysql.connector.connect(user='root', password='password',
                              host='localhost', database='openai')
cursor = cnx.cursor()

# Create a table to store the conversation history
cursor.execute("""
     CREATE TABLE IF NOT EXISTS conversation_history (
         id INT AUTO_INCREMENT PRIMARY KEY,
         message TEXT,
         is_user BOOLEAN
     )
 """)

if "history" not in st.session_state:
    # Retrieve the conversation history from the database
    cursor.execute("SELECT message, is_user FROM conversation_history")
    rows = cursor.fetchall()
    st.session_state.history = [{"message": row[0], "is_user": row[1]} for row in rows]

st.sidebar.markdown("## Configuration")
KEY = st.sidebar.text_input("Enter Your OpenAI API Key", placeholder="API Key", value="")
models = ['text-davinci-003', 'text-curie-001', 'text-babbage-001', 'text-ada-001']
model = st.sidebar.selectbox("Select a model", models, index=0)

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
max_tokens = st.sidebar.slider("Max Tokens", 0, 4000, 1786)

if st.sidebar.button("Delete Conversation"):
    # Clear the conversation history and delete the rows from the database
    cursor.execute("TRUNCATE TABLE conversation_history")
    st.session_state.history = []

if st.sidebar.button("Display Conversation"):
    for chat in st.session_state.history:
        if chat['is_user']:
            st.write("User: ", chat['message'])
        else:
            st.write("Bot: ", chat['message'])



def generate_answer(prompt):
    API_KEY = KEY
    API_URL = "https://api.openai.com/v1/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + API_KEY
    }
    previous_messages = [chat['message'] for chat in st.session_state.history if not chat['is_user']]
    previous_messages_text = '\n'.join(previous_messages)
    full_prompt = previous_messages_text + '\n' + prompt if previous_messages_text else prompt
    data = {
        "model": model,
        "prompt": full_prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    if not API_KEY:
        st.warning("Please input your API key")
        return
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    result = response.json()
    if 'choices' in result:
        message_bot = result['choices'][0]['text'].strip()
        st.session_state.history.append({"message": prompt, "is_user": True})
        st.session_state.history.append({"message": message_bot, "is_user": False})
        # Insert the new message into the database
        cursor.execute("INSERT INTO conversation_history (message, is_user) VALUES (%s, %s)", (message_bot, False))
        cnx.commit()
    else:
        st.error(
            "An error occurred while processing the API response. If using a model other than text-davinci-003, then lower the Max Tokens.")


prompt = st.text_input("Prompt", placeholder="Prompt Here", value="")
if st.button("Submit"):
    generate_answer(prompt)
    with st.spinner("Waiting for the response from the bot..."):
        for chat in st.session_state.history:
            if chat['is_user']:
                st.markdown("<img src='https://i.ibb.co/zVSbGvb/585e4beacb11b227491c3399.png' width='50' height='50' style='float:right;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='float:right; padding:10px; background-color: #2E2E2E; border-radius:10px; margin:10px;'>{chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<img src='https://i.ibb.co/LZFvDND/5841c0bda6515b1e0ad75a9e-1.png' width='50' height='50' style='float:left;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='float:left; padding:10px; background-color: #2E2E2E; border-radius:10px; margin:10px;'>{chat['message']}</div>", unsafe_allow_html=True)