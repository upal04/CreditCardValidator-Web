# app.py
import streamlit as st
import datetime
import uuid
import json
import os

# File Storage Functions
APP_DIR = os.path.dirname(os.path.abspath(__file__))   # folder where app.py lives
DATA_FILE = os.path.join(APP_DIR, "users.json")       # users.json always saved here

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state["users"], f, indent=4)  # pretty format for readability

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            st.session_state["users"] = json.load(f)
    else:
        st.session_state["users"] = {}

# Helper Functions
def format_number(number):
    """Format card number in XXXX XXXX XXXX XXXX style"""
    return " ".join([number[i:i+4] for i in range(0, len(number), 4)])

def validate_card(expiry):
    """Check if a card is expired (MM/YY)."""
    try:
        mm, yy = expiry.split("/")
        mm, yy = int(mm), int(yy)
        if yy < 100:
            yy += 2000
        today = datetime.date.today()
        return (yy > today.year) or (yy == today.year and mm >= today.month)
    except:
        return False

def mask_number(number):
    """Show only last 4 digits."""
    return "**** **** **** " + number[-4:]

# Auth Functions
def login(username, password):
    users = st.session_state["users"]
    return username in users and users[username]["password"] == password

def register(username, password):
    if username in st.session_state["users"]:
        return False
    st.session_state["users"][username] = {"password": password, "cards": []}
    save_data()
    return True

# App Config
st.set_page_config(page_title="💳 Credit Card Manager", page_icon="💳", layout="centered")

# Load users data from file (first run only)
if "users" not in st.session_state:
    load_data()
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# Interface
st.markdown(
    "<h1 style='text-align:center;color:#1E90FF;'>💳 Credit Card Manager</h1>",
    unsafe_allow_html=True,
)

# If not logged in → show login/register/settings
if not st.session_state["current_user"]:
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "⚙️ Settings"])

    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login(username.strip(), password):
                st.session_state["current_user"] = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.subheader("Create a new account")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register"):
            if not new_user.strip() or not new_pass.strip():
                st.warning("Username and password cannot be empty!")
            elif register(new_user.strip(), new_pass):
                st.success("Account created! You can login now.")
            else:
                st.error("Username already exists.")

    # Developer Settings (Admin Dashboard)
    with tab3:
        st.subheader("👨‍💻 Developer Dashboard")
        dev_key = st.text_input("🔑 Enter Developer Key", type="password")

        if dev_key == "upal140404":  # change this to your secret key
            st.success("✅ Developer mode enabled")

            users_data = st.session_state["users"]

            # Show total users
            st.info(f"📊 Total Accounts: {len(users_data)}")

            # Summary table
            st.write("### 📋 Accounts Summary")
            for uname, details in users_data.items():
                st.write(f"- **{uname}** → {len(details['cards'])} card(s)")

            st.write("---")

            # Loop through all users with expanders
            for uname, details in users_data.items():
                with st.expander(f"👤 User: {uname}  |  Cards: {len(details['cards'])}"):
                    st.write("**Password (stored):**", details["password"])  # ⚠️ For dev only
                    st.write("**Total Cards:**", len(details["cards"]))

                    # List all cards
                    for i, card in enumerate(details["cards"], start=1):
                        st.write(f"--- Card {i} ---")
                        st.write("Holder:", card["holder"])
                        st.write("Number:", format_number(card["number"]))
                        st.write("Expiry:", card["expiry"])
                        st.write("CVV:", card["cvv"])

# If logged in → dashboard
else:
    user = st.session_state["current_user"]
    st.sidebar.success(f"👤 Logged in as {user}")

    menu = st.sidebar.radio("📌 Menu", ["Add Card", "See Cards", "Delete Account", "Logout"])

    # Add Card
    if menu == "Add Card":
        st.subheader("➕ Add a New Card")
        holder = st.text_input("Cardholder Name", placeholder="Upal Pramanik")
        number = st.text_input("Card Number ", placeholder="1234 5678 9012 3456").replace(" ", "").replace("-", "")
        expiry = st.text_input("Expiry (MM/YY)", placeholder="04/2004")
        cvv = st.text_input("CVV", type="password", placeholder="123")

        if st.button("Save Card"):
            if not (holder and number and expiry and cvv):
                st.warning("All fields required.")
            elif not number.isdigit() or len(number) != 16:
                st.error("Card number must be 16 digits.")
            elif not cvv.isdigit() or len(cvv) != 3:
                st.error("CVV must be 3 digits.")
            else:
                card = {
                    "id": uuid.uuid4().hex,
                    "holder": holder,
                    "number": number,
                    "expiry": expiry,
                    "cvv": cvv,
                }
                st.session_state["users"][user]["cards"].append(card)
                save_data()
                st.success("Card saved!")

    # See Cards
    elif menu == "See Cards":
        st.subheader("📂 Your Saved Cards")
        cards = st.session_state["users"][user]["cards"]

        if not cards:
            st.info("No cards saved yet.")
        else:
            for i, card in enumerate(cards):
                with st.expander(f"💳 Card {i+1}: {mask_number(card['number'])}"):
                    st.write("**Holder:**", card["holder"])
                    st.write("**Expiry:**", card["expiry"])
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("👁️ Show Details", key=f"details_{card['id']}"):
                            st.info(
                            f"**Cardholder:** {card['holder']}\n\n"
                            f"**Number:** {format_number(card['number'])}\n\n"
                            f"**Expiry:** {card['expiry']}\n\n"
                            f"**CVV:** {card['cvv']}"
                        )
            
                    with col2:
                        if st.button("✅ Check Validity", key=f"validity_{card['id']}"):
                            if validate_card(card['expiry']):
                                st.success("Card is valid")
                            else:
                                st.error("Invalid Card: Your Credit Card has expired!")
            
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{card['id']}"):
                            st.session_state["users"][user]["cards"].remove(card)
                            save_data()
                            st.success("Card deleted")
                            st.rerun()

    # Delete Account
    elif menu == "Delete Account":
        st.subheader("⚠️ Delete Account Permanently")
        st.warning("This action cannot be undone. All your cards will be permanently deleted.")
        if st.checkbox("I confirm to delete my account and all cards"):
            if st.button("Delete My Account"):
                st.session_state["users"].pop(user, None)
                st.session_state["current_user"] = None
                save_data()
                st.success("Your account has been deleted.")
                st.rerun()

    # Logout
    elif menu == "Logout":
        st.session_state["current_user"] = None
        st.success("You have been logged out.")
        st.rerun()

    # Show card count in sidebar
    card_count = len(st.session_state["users"][user]["cards"])
    st.sidebar.info(f"📊 You have {card_count} saved card(s)")
