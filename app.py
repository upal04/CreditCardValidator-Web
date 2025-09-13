import streamlit as st
import json
import os

USER_DATA_FILE = "users.json"

# -------------------- Helper Functions --------------------
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def validate_card_number(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

# -------------------- Streamlit App --------------------
st.title("💳 Credit Card Manager")

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.guest = False

# -------------------- Login/Register/Guest --------------------
if not st.session_state.logged_in and not st.session_state.guest:
    option = st.radio("Choose an option:", ["Login", "Register", "Continue as Guest"])

    if option == "Login":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                if username in users and users[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                else:
                    st.error("Invalid username or password.")

    elif option == "Register":
        with st.form("register_form"):
            username = st.text_input("Choose Username")
            password = st.text_input("Choose Password", type="password")
            register_btn = st.form_submit_button("Register")
            if register_btn:
                if not username or not password:
                    st.warning("⚠️ Username and Password cannot be empty.")
                elif username in users:
                    st.warning("Username already exists.")
                else:
                    users[username] = {"password": password, "cards": []}
                    save_users(users)
                    st.success("Account created successfully! Please login.")

    elif option == "Continue as Guest":
        st.session_state.guest = True
        st.success("Guest mode enabled. Data won’t be saved.")

# -------------------- Guest Mode --------------------
elif st.session_state.guest:
    st.sidebar.title("👋 Guest Mode")
    menu = st.sidebar.radio("Menu", ["Validate a Card", "Logout"])

    if menu == "Validate a Card":
        st.subheader("🔎 Validate Card (Guest Mode)")
        with st.form("guest_card_form"):
            card_number = st.text_input("Card Number")
            expiry_date = st.text_input("Expiry Date (MM/YY)")
            cvv = st.text_input("CVV", type="password")
            holder = st.text_input("Cardholder Name")
            submit_btn = st.form_submit_button("Check Card")
            if submit_btn:
                if not card_number or not expiry_date or not cvv or not holder:
                    st.warning("⚠️ All fields are required.")
                else:
                    valid_status = "✅ Valid" if validate_card_number(card_number) else "❌ Invalid"
                    st.success("Card Checked (not saved):")
                    st.write(f"**Cardholder:** {holder}")
                    st.write(f"**Number:** {card_number}")
                    st.write(f"**Expiry:** {expiry_date}")
                    st.write(f"**CVV:** {cvv}")
                    st.write(f"**Status:** {valid_status}")

    elif menu == "Logout":
        st.session_state.guest = False
        st.success("Logged out from Guest mode.")

# -------------------- Logged-In Users --------------------
elif st.session_state.logged_in:
    st.sidebar.title(f"👋 Hello, {st.session_state.username}")
    menu = st.sidebar.radio("Menu", ["Add New Card", "View Cards", "Delete Card", "Delete Account", "Logout"])

    # Add New Card
    if menu == "Add New Card":
        st.subheader("➕ Add New Card")
        with st.form("add_card_form"):
            card_number = st.text_input("Card Number")
            expiry_date = st.text_input("Expiry Date (MM/YY)")
            cvv = st.text_input("CVV", type="password")
            holder = st.text_input("Cardholder Name")
            save_btn = st.form_submit_button("Save Card")
            if save_btn:
                if not card_number or not expiry_date or not cvv or not holder:
                    st.warning("⚠️ All fields are required.")
                else:
                    valid_status = "✅ Valid" if validate_card_number(card_number) else "❌ Invalid"
                    card = {
                        "number": card_number,
                        "expiry": expiry_date,
                        "cvv": cvv,
                        "holder": holder,
                        "status": valid_status
                    }
                    users[st.session_state.username]["cards"].append(card)
                    save_users(users)
                    st.success("Card saved successfully!")

    # View Cards
    elif menu == "View Cards":
        st.subheader("📋 Your Cards")
        cards = users[st.session_state.username]["cards"]
        if not cards:
            st.info("No cards saved yet.")
        else:
            for i, card in enumerate(cards, 1):
                st.write(f"### Card {i}")
                st.write(f"**Cardholder:** {card['holder']}")
                st.write(f"**Number:** {card['number']}")
                st.write(f"**Expiry:** {card['expiry']}")
                st.write(f"**CVV:** {card['cvv']}")
                st.write(f"**Status:** {card['status']}")
                st.markdown("---")

    # Delete Card
    elif menu == "Delete Card":
        st.subheader("🗑️ Delete a Card")
        cards = users[st.session_state.username]["cards"]
        if not cards:
            st.info("No cards available to delete.")
        else:
            card_index = st.selectbox("Select a card to delete", range(len(cards)))
            if st.button("Delete Selected Card"):
                removed = users[st.session_state.username]["cards"].pop(card_index)
                save_users(users)
                st.success(f"Deleted card: {removed['number']}")

    # Delete Account
    elif menu == "Delete Account":
        st.subheader("⚠️ Delete Account")
        if st.button("Delete My Account"):
            del users[st.session_state.username]
            save_users(users)
            st.session_state.logged_in = False
            st.session_state.username = None
            st.success("Account deleted successfully.")

    # Logout
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.success("Logged out successfully.")
