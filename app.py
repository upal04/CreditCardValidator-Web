import streamlit as st
import sqlite3
import hashlib
import datetime

DB_PATH = "credit_manager.db"

# ---------------------------
# Database setup
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            number TEXT,
            expiry_month TEXT,
            expiry_year TEXT,
            cvv TEXT,
            card_type TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

# ---------------------------
# Security helpers
# ---------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# ---------------------------
# Card helpers
# ---------------------------
def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number[::-1]]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def get_card_type(number: str) -> str:
    if number.startswith("4"):
        return "Visa"
    elif number.startswith(("51","52","53","54","55")):
        return "MasterCard"
    elif number.startswith(("34","37")):
        return "American Express"
    elif number.startswith("6"):
        return "Discover"
    return "Unknown"

# ---------------------------
# Session init
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = None   # {id, username}
if "guest" not in st.session_state:
    st.session_state.guest = False

# ---------------------------
# Pages
# ---------------------------
def page_auth():
    st.title("🔐 Login / Register / Guest")

    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Guest"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT id, password FROM users WHERE username=?", (username,))
            row = c.fetchone()
            conn.close()
            if row and verify_password(password, row[1]):
                st.session_state.user = {"id": row[0], "username": username}
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        username = st.text_input("New Username", key="reg_user")
        password = st.text_input("New Password", type="password", key="reg_pwd")
        if st.button("Register"):
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                          (username, hash_password(password), datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
                st.success("Account created! Please log in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists.")

    with tab3:
        if st.button("Continue as Guest"):
            st.session_state.guest = True
            st.success("You are in guest mode")
            st.experimental_rerun()

def page_add_card():
    st.title("➕ Add New Card")
    card_number = st.text_input("Card Number")
    expiry_month = st.text_input("Expiry Month (MM)")
    expiry_year = st.text_input("Expiry Year (YYYY)")
    cvv = st.text_input("CVV", type="password")

    if st.button("Save Card"):
        if not luhn_check(card_number):
            st.error("Invalid card number (Luhn check failed)")
        else:
            card_type = get_card_type(card_number)
            if st.session_state.guest:
                st.info(f"Guest mode: Card not saved. ✅ Card type: {card_type}")
            else:
                conn = get_connection()
                c = conn.cursor()
                c.execute("""INSERT INTO cards (user_id, number, expiry_month, expiry_year, cvv, card_type, created_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (st.session_state.user["id"], card_number, expiry_month, expiry_year, cvv, card_type,
                           datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
                st.success(f"Card saved! ✅ Type: {card_type}")

def page_view_cards():
    st.title("📋 See Card Details")
    if st.session_state.guest:
        st.info("Guest mode: No saved cards.")
        return
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, number, expiry_month, expiry_year, card_type, created_at FROM cards WHERE user_id=?",
              (st.session_state.user["id"],))
    rows = c.fetchall()
    conn.close()
    if not rows:
        st.info("No cards saved.")
    else:
        for row in rows:
            st.write(f"**ID {row[0]}** | {row[1]} | {row[4]} | Exp: {row[2]}/{row[3]} | Added: {row[5]}")

def page_delete_card():
    st.title("🗑️ Delete Card")
    if st.session_state.guest:
        st.info("Guest mode: No cards to delete.")
        return
    card_id = st.number_input("Enter Card ID to delete", step=1, min_value=1)
    if st.button("Delete"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM cards WHERE id=? AND user_id=?", (card_id, st.session_state.user["id"]))
        conn.commit()
        conn.close()
        st.success("Card deleted (if ID was valid).")

def page_delete_account():
    st.title("⚠️ Delete Account")
    if st.session_state.guest:
        st.info("Guest mode: No account to delete.")
        return
    if st.button("Delete My Account"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=?", (st.session_state.user["id"],))
        conn.commit()
        conn.close()
        st.session_state.user = None
        st.success("Account deleted permanently.")
        st.experimental_rerun()

# ---------------------------
# Main
# ---------------------------
def main():
    init_db()

    if not st.session_state.user and not st.session_state.guest:
        page_auth()
        return

    menu = ["Add Card", "See Cards", "Delete Card", "Delete Account", "Logout"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "Add Card":
        page_add_card()
    elif choice == "See Cards":
        page_view_cards()
    elif choice == "Delete Card":
        page_delete_card()
    elif choice == "Delete Account":
        page_delete_account()
    elif choice == "Logout":
        st.session_state.user = None
        st.session_state.guest = False
        st.success("Logged out")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
