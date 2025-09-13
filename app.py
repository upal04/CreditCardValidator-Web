# app.py
import streamlit as st
import datetime
import uuid

def format_number(number):
    """Format card number in XXXX XXXX XXXX XXXX style"""
    return " ".join([number[i:i+4] for i in range(0, len(number), 4)])

st.set_page_config(page_title="💳 Credit Card Manager", page_icon="💳", layout="centered")

# -------------------------
# Session Storage
# -------------------------
if "users" not in st.session_state:
    st.session_state["users"] = {}
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None


# -------------------------
# Helper Functions
# -------------------------
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


# -------------------------
# Auth Functions
# -------------------------
def login(username, password):
    users = st.session_state["users"]
    return username in users and users[username]["password"] == password


def register(username, password):
    if username in st.session_state["users"]:
        return False
    st.session_state["users"][username] = {"password": password, "cards": []}
    return True


# -------------------------
# Interface
# -------------------------
st.markdown(
    "<h1 style='text-align:center;color:#1E90FF;'>💳 Credit Card Manager</h1>",
    unsafe_allow_html=True,
)

# -------------------------
# If not logged in → show login/register
# -------------------------
if not st.session_state["current_user"]:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

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

# -------------------------
# If logged in → dashboard
# -------------------------
else:
    user = st.session_state["current_user"]
    st.sidebar.success(f"👤 Logged in as {user}")

    menu = st.sidebar.radio("📌 Menu", ["Add Card", "See Cards", "Delete Account", "Logout"])

    # ------------------ Add Card ------------------
    if menu == "Add Card":
        st.subheader("➕ Add a New Card")
        holder = st.text_input("Cardholder Name")
        number = st.text_input("Card Number ").replace(" ", "").replace("-", "")
        expiry = st.text_input("Expiry (MM/YY)")
        cvv = st.text_input("CVV", type="password")

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
                st.success("Card saved!")

    # ------------------ See Cards ------------------
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
                        if st.button("Show Full Details", key=f"details_{card['id']}"):
                            st.info(
                                f"Holder: {card['holder']} \n"
                                f"\nNumber: {format_number(card['number'])} \n"
                                f"\nExpiry: {card['expiry']} \n"
                                f"\nCVV: {card['cvv']}"
                            )

                    with col2:
                        if st.button("Check Validity", key=f"validity_{card['id']}"):
                            if validate_card(card["expiry"]):
                                st.success("✅ Card is Valid")
                            else:
                                st.error("❌ Invalid Card. Your Credit Card is Expired!")

                    with col3:
                        if st.button("Delete Card", key=f"delete_{card['id']}"):
                            st.session_state["users"][user]["cards"].remove(card)
                            st.warning("Card deleted.")
                            st.rerun()

    # ------------------ Delete Account ------------------
    elif menu == "Delete Account":
        st.subheader("⚠️ Delete Account Permanently")
        if st.checkbox("I confirm to delete my account and all cards"):
            if st.button("Delete My Account"):
                st.session_state["users"].pop(user, None)
                st.session_state["current_user"] = None
                st.success("Your account has been deleted.")
                st.rerun()

    # ------------------ Logout ------------------
    elif menu == "Logout":
        st.session_state["current_user"] = None
        st.success("You have been logged out.")
        st.rerun()





