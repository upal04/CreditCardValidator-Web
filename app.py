import streamlit as st
import datetime
import uuid
import sqlite3
import os
import re

# Database Setup
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "users.db")

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            holder TEXT NOT NULL,
            number TEXT NOT NULL,
            expiry TEXT NOT NULL,
            cvv TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    conn.commit()
    conn.close()

def load_users():
    """Load all users and their cards into session_state."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users")
    users = {row[0]: {"password": row[1], "cards": []} for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, username, holder, number, expiry, cvv FROM cards")
    for row in cursor.fetchall():
        card = {
            "id": row[0],
            "holder": row[1],
            "number": row[2],
            "expiry": row[3],
            "cvv": row[4]
        }
        users[row[1]]["cards"].append(card)
    
    conn.close()
    return users

def save_user(username, password):
    """Save a new user to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def save_card(username, card):
    """Save a card for a user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cards (id, username, holder, number, expiry, cvv) VALUES (?, ?, ?, ?, ?, ?)",
                   (card["id"], username, card["holder"], card["number"], card["expiry"], card["cvv"]))
    conn.commit()
    conn.close()

def delete_user(username):
    """Delete a user and all their cards."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE username = ?", (username,))
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def delete_card(card_id):
    """Delete a specific card."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()

# Helper Functions
def format_number(number):
    """Format card number in XXXX XXXX XXXX XXXX style."""
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

def validate_password_strength(password):
    """Check if password is strong enough."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (e.g., !@#$%^&*)."
    return True, "Password is strong."

def validate_credit_card_number(number):
    """Validate credit card number using Luhn algorithm."""
    if not number.isdigit() or len(number) != 16:
        return False
    # Luhn algorithm
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    return luhn_checksum(int(number))

# Auth Functions
def login(username, password):
    users = st.session_state["users"]
    return username in users and users[username]["password"] == password

def register(username, password):
    if username in st.session_state["users"]:
        return False, "Username already exists."
    is_strong, msg = validate_password_strength(password)
    if not is_strong:
        return False, msg
    save_user(username, password)
    st.session_state["users"][username] = {"password": password, "cards": []}
    return True, "Account created successfully!"

# App Config
st.set_page_config(page_title="💳 Credit Card Manager", page_icon="💳", layout="centered")

# Initialize DB and load data
init_db()
if "users" not in st.session_state:
    st.session_state["users"] = load_users()
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
            else:
                success, msg = register(new_user.strip(), new_pass)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    # Developer Settings (Admin Dashboard)
    with tab3:
        st.subheader("👨‍💻 Developer Dashboard")
        dev_key = st.text_input("🔑 Enter Developer Key", type="password")

        if dev_key == "upal140404":  # Change this to your secret key
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
        number = st.text_input("Card Number", placeholder="1234 5678 9012 3456").replace(" ", "").replace("-", "")
        expiry = st.text_input("Expiry (MM/YY)", placeholder="04/24")
        cvv = st.text_input("CVV", type="password", placeholder="123")

        if st.button("Save Card"):
            if not (holder and number and expiry and cvv):
                st.warning("All fields are required.")
            elif not validate_credit_card_number(number):
                st.error("Invalid card number. It must be a valid 16-digit credit card number.")
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
                save_card(user, card)
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
                                st.success("Card is Valid!")
                            else:
                                st.error("Invalid Card: Your Credit Card has expired!")
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{card['id']}"):
                            st.session_state["users"][user]["cards"].remove(card)
                            delete_card(card['id'])
                            st.success("Card deleted")
                            st.rerun()

    # Delete Account
    elif menu == "Delete Account":
        st.subheader("⚠️ Delete Account Permanently")
        st.warning("This action cannot be undone. All your cards will be permanently deleted.")
        if st.checkbox("I confirm to delete my account and all cards"):
            if st.button("Delete My Account"):
                delete_user(user)
                st.session_state["users"].pop(user, None)
                st.session_state["current_user"] = None
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
