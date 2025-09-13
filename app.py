import streamlit as st
import json
import os
from datetime import datetime

# ---------------- Database Helpers ----------------
DB_FILE = "users.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- Card Validation ----------------
def validate_card(number, expiry):
    # Check expiry
    try:
        exp_month, exp_year = map(int, expiry.split("/"))
        now = datetime.now()
        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
            return False
    except:
        return False
    # Check length of card number
    return len(number.replace(" ", "")) in [13, 15, 16]

# ---------------- Session ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

data = load_data()

# ---------------- Auth Pages ----------------
def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in data and data[username]["password"] == password:
            st.session_state.user = username
            st.session_state.page = "dashboard"
            st.success("Login successful ✅")
        else:
            st.error("Invalid username or password!")

def register():
    st.title("📝 Register")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    confirm = st.text_input("Confirm password", type="password")
    if st.button("Register"):
        if not username or not password:
            st.error("Username and password cannot be empty!")
        elif password != confirm:
            st.error("Passwords do not match!")
        elif username in data:
            st.error("Username already exists!")
        else:
            data[username] = {"password": password, "cards": []}
            save_data(data)
            st.success("Account created successfully! Please login.")
            st.session_state.page = "login"

# ---------------- Dashboard ----------------
def dashboard():
    st.sidebar.title(f"👋 Hello, {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["Add New Card", "View Cards", "Delete Card", "Delete Account", "Logout"])

    user_cards = data[st.session_state.user]["cards"]

    if menu == "Add New Card":
        st.title("➕ Add New Card")
        holder = st.text_input("Cardholder Name")
        number = st.text_input("Card Number (digits only)")
        expiry = st.text_input("Expiry (MM/YYYY)")
        cvv = st.text_input("CVV", type="password")

        if st.button("Save Card"):
            if holder and number and expiry and cvv:
                data[st.session_state.user]["cards"].append({
                    "holder": holder,
                    "number": number,
                    "expiry": expiry,
                    "cvv": cvv
                })
                save_data(data)
                st.success("Card saved successfully!")
            else:
                st.error("All fields are required!")

    elif menu == "View Cards":
        st.title("💳 Your Cards")
        if not user_cards:
            st.info("No cards saved yet.")
        else:
            for i, card in enumerate(user_cards, 1):
                st.subheader(f"Card {i}")
                st.write(f"**Cardholder:** {card['holder']}")
                st.write(f"**Number:** **** **** **** {card['number'][-4:]}")
                st.write(f"**Expiry:** {card['expiry']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Show Full Details {i}"):
                        st.info(f"""
                        **Cardholder:** {card['holder']}  
                        **Number:** {card['number']}  
                        **Expiry:** {card['expiry']}  
                        **CVV:** {card['cvv']}  
                        """)
                with col2:
                    if st.button(f"Check Validity {i}"):
                        if validate_card(card['number'], card['expiry']):
                            st.success("✅ Card is Valid")
                        else:
                            st.error("❌ Card is Expired / Invalid")

                st.markdown("---")

    elif menu == "Delete Card":
        st.title("🗑️ Delete Card")
        if not user_cards:
            st.info("No cards available to delete.")
        else:
            choice = st.selectbox("Select card to delete", [f"Card {i+1}" for i in range(len(user_cards))])
            if st.button("Delete"):
                idx = int(choice.split()[1]) - 1
                user_cards.pop(idx)
                save_data(data)
                st.success("Card deleted successfully!")

    elif menu == "Delete Account":
        st.title("⚠️ Delete Account")
        if st.button("Delete My Account"):
            del data[st.session_state.user]
            save_data(data)
            st.session_state.user = None
            st.session_state.page = "login"
            st.success("Account deleted successfully!")

    elif menu == "Logout":
        st.session_state.user = None
        st.session_state.page = "login"
        st.success("Logged out successfully!")

# ---------------- Router ----------------
if st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
elif st.session_state.page == "dashboard":
    dashboard()

# ---------------- Navigation ----------------
if st.session_state.page == "login":
    if st.button("New user? Register here"):
        st.session_state.page = "register"
elif st.session_state.page == "register":
    if st.button("Already have an account? Login here"):
        st.session_state.page = "login"
