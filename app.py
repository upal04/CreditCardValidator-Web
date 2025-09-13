import streamlit as st
import json
import os
from datetime import datetime

# ==========================
# Utility Functions
# ==========================
USERS_FILE = "users.json"


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def validate_card(card_number: str, expiry_date: str) -> str:
    """Validate card number using Luhn and expiry date."""
    # --- Luhn Check ---
    digits = [int(d) for d in card_number if d.isdigit()]
    if not digits:
        return "❌ Invalid Number"
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    luhn_valid = (checksum % 10 == 0)

    # --- Expiry Check ---
    try:
        exp_month, exp_year = expiry_date.split("/")
        exp_month = int(exp_month)
        exp_year = int("20" + exp_year) if len(exp_year) == 2 else int(exp_year)

        today = datetime.today()
        expiry = datetime(exp_year, exp_month, 1)
        not_expired = expiry >= datetime(today.year, today.month, 1)
    except Exception:
        return "❌ Invalid Expiry Format"

    if not luhn_valid:
        return "❌ Invalid Number"
    if not not_expired:
        return "❌ Expired"
    return "✅ Valid"


# ==========================
# Pages
# ==========================
def page_auth(users):
    st.title("🔐 Login / Register / Guest")

    tab_login, tab_register, tab_guest = st.tabs(["Login", "Register", "Guest"])

    # --- Login ---
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                if username in users and users[username]["password"] == password:
                    st.session_state["user"] = username
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

    # --- Register ---
    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            register_btn = st.form_submit_button("Register")

            if register_btn:
                if not new_username or not new_password:
                    st.warning("⚠️ Please fill in all fields")
                elif new_username in users:
                    st.error("❌ Username already exists")
                else:
                    users[new_username] = {"password": new_password, "cards": []}
                    save_users(users)
                    st.success("✅ Account created successfully! Please login.")

    # --- Guest ---
    with tab_guest:
        if st.button("Continue as Guest"):
            st.session_state["user"] = "guest"
            st.info("ℹ️ Guest mode: You can only view cards, not save/delete.")
            st.rerun()


def page_dashboard(users):
    username = st.session_state["user"]
    st.sidebar.title(f"👋 Hello, {username}")
    menu = st.sidebar.radio("Menu", ["Add New Card", "View Cards", "Delete Card", "Delete Account", "Logout"])

    # Guest restriction
    if username == "guest" and menu in ["Add New Card", "Delete Card", "Delete Account"]:
        st.warning("⚠️ Guests cannot perform this action. Please register or login.")
        return

    # --- Add Card ---
    if menu == "Add New Card":
        st.header("➕ Add New Card")
        with st.form("add_card_form"):
            holder = st.text_input("Cardholder Name")
            card_number = st.text_input("Card Number")
            expiry_date = st.text_input("Expiry Date (MM/YYYY)")
            cvv = st.text_input("CVV", type="password")
            save_btn = st.form_submit_button("Save Card")

            if save_btn:
                if not holder or not card_number or not expiry_date or not cvv:
                    st.warning("⚠️ Please fill in all fields")
                else:
                    status = validate_card(card_number, expiry_date)
                    card = {
                        "holder": holder,
                        "number": card_number,
                        "expiry": expiry_date,
                        "cvv": cvv,
                        "status": status,
                    }
                    users[username]["cards"].append(card)
                    save_users(users)
                    st.success(f"✅ Card saved! Status: {status}")

    # --- View Cards ---
    elif menu == "View Cards":
        st.header("💳 Your Saved Cards")
        cards = users.get(username, {}).get("cards", [])
        if not cards:
            st.info("ℹ️ No cards saved yet.")
        else:
            for i, card in enumerate(cards, 1):
                st.subheader(f"Card {i}")
                st.write(f"**Cardholder:** {card['holder']}")
                st.write(f"**Number:** {card['number']}")
                st.write(f"**Expiry:** {card['expiry']}")
                st.write(f"**CVV:** {card['cvv']}")
                st.write(f"**Status:** {card['status']}")
                st.markdown("---")

    # --- Delete Card ---
    elif menu == "Delete Card":
        st.header("🗑️ Delete Card")
        cards = users[username]["cards"]
        if not cards:
            st.info("ℹ️ No cards to delete.")
        else:
            options = [f"{c['holder']} - {c['number']}" for c in cards]
            choice = st.selectbox("Select a card to delete", options)
            if st.button("Delete Selected Card"):
                idx = options.index(choice)
                del users[username]["cards"][idx]
                save_users(users)
                st.success("✅ Card deleted successfully")
                st.rerun()

    # --- Delete Account ---
    elif menu == "Delete Account":
        st.header("⚠️ Delete Account")
        if st.button("Delete My Account"):
            del users[username]
            save_users(users)
            st.session_state.pop("user")
            st.success("✅ Account deleted successfully")
            st.rerun()

    # --- Logout ---
    elif menu == "Logout":
        st.session_state.pop("user")
        st.success("✅ Logged out successfully")
        st.rerun()


# ==========================
# Main App
# ==========================
def main():
    st.set_page_config(page_title="Credit Card Manager", page_icon="💳", layout="wide")
    users = load_users()

    if "user" not in st.session_state:
        page_auth(users)
    else:
        page_dashboard(users)


if __name__ == "__main__":
    main()
