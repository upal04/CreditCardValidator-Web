import streamlit as st
import sqlite3
import hashlib

# ============== DATABASE ==============
def init_db():
    conn = sqlite3.connect("cards.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT,
            card_name TEXT,
            expiry TEXT,
            cvv TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# ============== AUTH ==============
def page_auth():
    st.title("🔐 Login / Register / Guest")
    tab_login, tab_register, tab_guest = st.tabs(["Login", "Register", "Guest"])

    # LOGIN
    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            conn = sqlite3.connect("cards.db")
            c = conn.cursor()
            c.execute("SELECT id, password FROM users WHERE username=?", (username,))
            row = c.fetchone()
            conn.close()
            if row and verify_password(password, row[1]):
                st.session_state.user = {"id": row[0], "username": username}
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # REGISTER
    with tab_register:
        new_username = st.text_input("New Username", key="reg_user")
        new_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            conn = sqlite3.connect("cards.db")
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                          (new_username, hash_password(new_password)))
                conn.commit()
                st.success("Account created! Please log in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists")
            conn.close()

    # GUEST
    with tab_guest:
        if st.button("Continue as Guest"):
            st.session_state.user = {"id": None, "username": "Guest"}
            st.success("Guest mode enabled")
            st.rerun()

# ============== CARD MANAGER ==============
def page_dashboard():
    st.title(f"💳 Credit Card Manager ({st.session_state.user['username']})")
    choice = st.sidebar.radio("Menu", ["Add Card", "View Cards", "Delete Card", "Account Settings", "Logout"])

    # ADD CARD
    if choice == "Add Card":
        card_number = st.text_input("Card Number")
        card_name = st.text_input("Card Holder Name")
        expiry = st.text_input("Expiry Date (MM/YY)")
        cvv = st.text_input("CVV", type="password")

        if st.button("Save Card"):
            if st.session_state.user["id"] is None:
                st.error("Guests cannot save cards. Please register or login.")
            else:
                conn = sqlite3.connect("cards.db")
                c = conn.cursor()
                c.execute("INSERT INTO cards (user_id, card_number, card_name, expiry, cvv) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state.user["id"], card_number, card_name, expiry, cvv))
                conn.commit()
                conn.close()
                st.success("Card saved successfully!")

    # VIEW CARDS
    elif choice == "View Cards":
        if st.session_state.user["id"] is None:
            st.warning("Guests cannot view cards. Please register or login.")
        else:
            conn = sqlite3.connect("cards.db")
            c = conn.cursor()
            c.execute("SELECT id, card_number, card_name, expiry FROM cards WHERE user_id=?",
                      (st.session_state.user["id"],))
            rows = c.fetchall()
            conn.close()

            if rows:
                for row in rows:
                    st.write(f"**Card ID:** {row[0]} | **Number:** {row[1]} | **Name:** {row[2]} | **Expiry:** {row[3]}")
            else:
                st.info("No cards found.")

    # DELETE CARD
    elif choice == "Delete Card":
        if st.session_state.user["id"] is None:
            st.warning("Guests cannot delete cards. Please register or login.")
        else:
            card_id = st.number_input("Enter Card ID to delete", min_value=1, step=1)
            if st.button("Delete Card"):
                conn = sqlite3.connect("cards.db")
                c = conn.cursor()
                c.execute("DELETE FROM cards WHERE id=? AND user_id=?", (card_id, st.session_state.user["id"]))
                conn.commit()
                conn.close()
                st.success(f"Card {card_id} deleted successfully!")

    # ACCOUNT SETTINGS
    elif choice == "Account Settings":
        if st.session_state.user["id"] is None:
            st.warning("Guests do not have account settings.")
        else:
            if st.button("Delete Account ❌"):
                conn = sqlite3.connect("cards.db")
                c = conn.cursor()
                c.execute("DELETE FROM users WHERE id=?", (st.session_state.user["id"],))
                c.execute("DELETE FROM cards WHERE user_id=?", (st.session_state.user["id"],))
                conn.commit()
                conn.close()
                st.success("Account deleted permanently.")
                st.session_state.user = None
                st.rerun()

    # LOGOUT
    elif choice == "Logout":
        st.session_state.user = None
        st.success("Logged out successfully.")
        st.rerun()

# ============== MAIN ==============
def main():
    st.set_page_config(page_title="Credit Card Manager", page_icon="💳", layout="centered")
    init_db()

    if "user" not in st.session_state or st.session_state.user is None:
        page_auth()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
