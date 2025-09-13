import streamlit as st
import json
import os

# -------------------- JSON DATA --------------------
DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": {}}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- Luhn & Card Type --------------------
def luhn_check(card_number):
    digits = [int(d) for d in card_number[::-1]]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def get_card_type(number):
    if number.startswith("4"):
        return "Visa"
    elif number.startswith(("51","52","53","54","55")):
        return "MasterCard"
    elif number.startswith(("34","37")):
        return "American Express"
    elif number.startswith("6"):
        return "Discover"
    else:
        return "Unknown"

# -------------------- SESSION STATE --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "guest" not in st.session_state:
    st.session_state.guest = False
if "page" not in st.session_state:
    st.session_state.page = "home"  # home/login/register/guest/main

# -------------------- AUTH FUNCTIONS --------------------
def register(username, password):
    data = load_data()
    if username in data["users"]:
        st.error("Username already exists!")
        return False
    data["users"][username] = {"password": password, "cards": []}
    save_data(data)
    st.success("Registered successfully! You can now login.")
    st.session_state.page = "home"
    return True

def login(username, password):
    data = load_data()
    if username in data["users"] and data["users"][username]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.guest = False
        st.session_state.page = "main"
        st.success(f"Logged in as {username}")
        return True
    else:
        st.error("Invalid username or password")
        return False

def guest_login():
    st.session_state.logged_in = True
    st.session_state.guest = True
    st.session_state.username = "Guest"
    st.session_state.page = "main"
    st.success("Logged in as Guest (cards will not be saved)")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.guest = False
    st.session_state.page = "home"
    st.info("Logged out successfully")

# -------------------- STREAMLIT CONFIG --------------------
st.set_page_config(page_title="💳 Credit Card Manager", page_icon="💳", layout="centered")
st.title("💳 Credit Card Manager")

# -------------------- PAGE LOGIC --------------------
# Home Page
if st.session_state.page == "home":
    st.subheader("Welcome! Please choose an option:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Login"):
            st.session_state.page = "login"
    with col2:
        if st.button("Register"):
            st.session_state.page = "register"
    with col3:
        if st.button("Guest"):
            guest_login()

# Login Page
elif st.session_state.page == "login":
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        login(username, password)
    if st.button("Back"):
        st.session_state.page = "home"

# Register Page
elif st.session_state.page == "register":
    st.subheader("Register")
    username = st.text_input("New Username", key="reg_user")
    password = st.text_input("New Password", type="password", key="reg_pass")
    if st.button("Register"):
        register(username, password)
    if st.button("Back"):
        st.session_state.page = "home"

# Main App Page
elif st.session_state.page == "main":
    st.sidebar.write(f"👤 User: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()
    
    # Load user cards safely
    data = load_data()
    if not st.session_state.guest:
        user_data = data["users"].get(st.session_state.username, {})
        user_cards = user_data.get("cards", [])
    else:
        user_cards = []

    # Menu
    menu = ["Your Credit Cards", "Add New Credit Card", "Delete Credit Card"]
    choice = st.selectbox("Select Option", menu)

    # -------------------- YOUR CREDIT CARDS --------------------
    if choice == "Your Credit Cards":
        st.subheader("Your Saved Credit Cards")
        if len(user_cards) == 0:
            st.info("No cards saved yet. Please add a new credit card.")
        else:
            for idx, card in enumerate(user_cards):
                st.markdown(f"**Card {idx+1}: {card['owner_name']}**")
                st.write(f"Number: {card['number']}")
                st.write(f"Expiration: {card['month']}/{card['year']}")
                st.write(f"CVV: {card['cvv']}")
                st.write(f"Type: {get_card_type(card['number'])}")
                valid = "✅ Valid" if luhn_check(card['number']) else "❌ Invalid"
                st.write(f"Luhn Check: {valid}")
                st.markdown("---")

    # -------------------- ADD NEW CREDIT CARD --------------------
    elif choice == "Add New Credit Card":
        st.subheader("Add a New Credit Card")
        owner_name = st.text_input("Owner Name / Card Nickname")
        card_number = st.text_input("Card Number").replace(" ", "").replace("-", "")
        month = st.text_input("Expiration Month (MM)")
        year = st.text_input("Expiration Year (YYYY)")
        cvv = st.text_input("CVV", type="password")
        if st.button("Add Card"):
            if not owner_name:
                st.error("Please enter Owner Name / Nickname")
            elif not (card_number.isdigit() and len(card_number) in [13,15,16]):
                st.error("Invalid card number format")
            elif not luhn_check(card_number):
                st.error("Invalid card number (failed Luhn check)")
            elif not (month.isdigit() and 1<=int(month)<=12):
                st.error("Invalid expiration month")
            elif not (year.isdigit() and len(year)==4):
                st.error("Invalid expiration year")
            elif not (cvv.isdigit() and len(cvv) in [3,4]):
                st.error("Invalid CVV")
            else:
                if not st.session_state.guest:
                    data["users"][st.session_state.username]["cards"].append({
                        "owner_name": owner_name,
                        "number": card_number,
                        "month": month,
                        "year": year,
                        "cvv": cvv
                    })
                    save_data(data)
                    st.success("Card added successfully!")
                else:
                    st.info("Guest mode: card not saved.")

    # -------------------- DELETE CREDIT CARD --------------------
    elif choice == "Delete Credit Card":
        st.subheader("Delete a Credit Card")
        if len(user_cards) == 0:
            st.info("No cards to delete.")
        else:
            options = [f"{c['owner_name']} ({c['number'][-4:]})" for c in user_cards]
            to_delete = st.selectbox("Select Card to Delete", options)
            if st.button("Delete Card"):
                if not st.session_state.guest:
                    idx = options.index(to_delete)
                    del data["users"][st.session_state.username]["cards"][idx]
                    save_data(data)
                    st.success("Card deleted successfully!")
                else:
                    st.info("Guest mode: no cards saved, nothing to delete.")
