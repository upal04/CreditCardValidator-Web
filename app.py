import streamlit as st
import datetime

# ------------------------------
# Helper Functions
# ------------------------------

def validate_card(number, expiry):
    """Check if card is valid based on expiry date."""
    try:
        exp_month, exp_year = expiry.split("/")
        exp_month, exp_year = int(exp_month), int(exp_year)

        today = datetime.date.today()
        # Expiry means the last day of the month
        expiry_date = datetime.date(2000 + exp_year, exp_month, 1) + datetime.timedelta(days=31)
        expiry_date = expiry_date.replace(day=1) - datetime.timedelta(days=1)

        return today <= expiry_date
    except:
        return False

# ------------------------------
# Session State Initialization
# ------------------------------

if "users" not in st.session_state:
    st.session_state["users"] = {}  # {username: {"password": str, "cards": list}}

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# ------------------------------
# Authentication
# ------------------------------

def login(username, password):
    users = st.session_state["users"]
    if username in users and users[username]["password"] == password:
        st.session_state["current_user"] = username
        return True
    return False

def register(username, password):
    users = st.session_state["users"]
    if username not in users:
        users[username] = {"password": password, "cards": []}
        return True
    return False

# ------------------------------
# Main App
# ------------------------------

st.set_page_config(page_title="Card Manager", layout="centered")

st.title("💳 Simple Card Manager")

# If no user is logged in → show login/register
if not st.session_state["current_user"]:
    option = st.radio("Choose Action:", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            if login(username, password):
                st.success(f"Welcome back, {username}!")
            else:
                st.error("Invalid username or password.")
    else:
        if st.button("Register"):
            if username.strip() == "" or password.strip() == "":
                st.warning("Username and password cannot be empty!")
            elif register(username, password):
                st.success("Account created successfully! Please log in.")
            else:
                st.error("Username already exists. Try another one.")

else:
    # User dashboard
    user = st.session_state["current_user"]
    st.sidebar.success(f"Logged in as {user}")
    if st.sidebar.button("Logout"):
        st.session_state["current_user"] = None
        st.rerun()

    menu = st.sidebar.radio("Menu", ["Add Card", "View Cards"])

    # ------------------ Add Card ------------------
    if menu == "Add Card":
        st.subheader("➕ Add a New Card")

        holder = st.text_input("Cardholder Name")
        number = st.text_input("Card Number (16 digits)")
        expiry = st.text_input("Expiry Date (MM/YY)")
        cvv = st.text_input("CVV", type="password")

        if st.button("Save Card"):
            if not (holder and number and expiry and cvv):
                st.warning("All fields are required!")
            elif not number.isdigit() or len(number) != 16:
                st.error("Card number must be 16 digits.")
            elif not cvv.isdigit() or len(cvv) != 3:
                st.error("CVV must be 3 digits.")
            else:
                card = {"holder": holder, "number": number, "expiry": expiry, "cvv": cvv}
                st.session_state["users"][user]["cards"].append(card)
                st.success("Card saved successfully!")

    # ------------------ View Cards ------------------
    elif menu == "View Cards":
        st.subheader("📂 Your Saved Cards")
        cards = st.session_state["users"][user]["cards"]

        if not cards:
            st.info("No cards saved yet.")
        else:
            for i, card in enumerate(cards, 1):
                st.write(f"### Card {i}")
                st.write(f"**Cardholder:** {card['holder']}")
                st.write(f"**Number:** **** **** **** {card['number'][-4:]}")
                st.write(f"**Expiry:** {card['expiry']}")

                # Buttons with unique keys
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Show Full Details", key=f"details_{i}"):
                        st.info(f"""
                        **Cardholder:** {card['holder']}  
                        **Number:** {card['number']}  
                        **Expiry:** {card['expiry']}  
                        **CVV:** {card['cvv']}  
                        """)

                with col2:
                    if st.button("Check Validity", key=f"validity_{i}"):
                        if validate_card(card['number'], card['expiry']):
                            st.success("✅ Card is Valid")
                        else:
                            st.error("❌ Card is Expired / Invalid")

                with col3:
                    if st.button("Delete Card", key=f"delete_{i}"):
                        cards.pop(i - 1)
                        st.warning("Card deleted!")
                        st.rerun()

                st.markdown("---")
