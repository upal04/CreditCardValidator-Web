# app.py
import streamlit as st
import json
import os
import hashlib
import os as _os
from datetime import datetime
import uuid

# ---------------- Config ----------------
DATA_FILE = "data.json"

# ---------------- Helpers: Data ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"users": {}}
    return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- Helpers: Password ----------------
def hash_password(password, salt=None):
    """Return (salt, hashed) where salt is hex and hashed is hex SHA256(salt+password)."""
    if salt is None:
        salt = _os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, hashed

def create_user(username, password):
    data = load_data()
    if username in data["users"]:
        return False, "User already exists."
    salt, hashed = hash_password(password)
    data["users"][username] = {
        "salt": salt,
        "password": hashed,
        "cards": []
    }
    save_data(data)
    return True, "User registered successfully."

def authenticate(username, password):
    data = load_data()
    u = data["users"].get(username)
    if not u:
        return False
    salt = u["salt"]
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed == u["password"]

# ---------------- Card Utilities ----------------
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

def get_card_type_and_logo(number):
    if number.startswith("4"):
        return "Visa", "https://img.icons8.com/color/96/000000/visa.png"
    elif number.startswith(("51", "52", "53", "54", "55")):
        return "MasterCard", "https://img.icons8.com/color/96/000000/mastercard.png"
    elif number.startswith(("34", "37")):
        return "American Express", "https://img.icons8.com/color/96/000000/amex.png"
    elif number.startswith("6"):
        return "Discover", "https://img.icons8.com/color/96/000000/discover.png"
    else:
        return "Unknown", "https://img.icons8.com/ios-filled/100/credit-card.png"

def check_expiry(month, year):
    try:
        now = datetime.now()
        exp_date = datetime(int(year), int(month), 1)
    except Exception:
        return "InvalidDate"
    if exp_date < now:
        return "Expired"
    months_left = (exp_date.year - now.year) * 12 + (exp_date.month - now.month)
    if months_left <= 3:
        return "Expiring Soon"
    return "Valid"

# ---------------- Session helpers ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "guest" not in st.session_state:
    st.session_state.guest = False
if "guest_cards" not in st.session_state:
    st.session_state.guest_cards = []

def get_current_user_cards():
    if st.session_state.guest:
        return st.session_state.guest_cards
    data = load_data()
    user = data["users"].get(st.session_state.username)
    if not user:
        return []
    return user.get("cards", [])

def save_current_user_cards(cards):
    if st.session_state.guest:
        st.session_state.guest_cards = cards
        return
    data = load_data()
    if st.session_state.username not in data["users"]:
        data["users"][st.session_state.username] = {"salt": "", "password": "", "cards": []}
    data["users"][st.session_state.username]["cards"] = cards
    save_data(data)

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.guest = False

# ---------------- UI ----------------
st.set_page_config(page_title="Credit Card Manager (Multi-user)", layout="centered")
st.title("💳 Credit Card Manager (Private per user)")

# Sidebar: Authentication panel
st.sidebar.markdown("## 🔐 Account")
if not st.session_state.logged_in:
    auth_choice = st.sidebar.selectbox("Mode", ["Login", "Register", "Use as Guest (temporary)"])
    if auth_choice == "Login":
        li_user = st.sidebar.text_input("Username", key="li_user")
        li_pass = st.sidebar.text_input("Password", type="password", key="li_pass")
        if st.sidebar.button("Login"):
            if authenticate(li_user, li_pass):
                st.session_state.logged_in = True
                st.session_state.username = li_user
                st.session_state.guest = False
                st.sidebar.success(f"Logged in as {li_user}")
            else:
                st.sidebar.error("Invalid credentials.")
    elif auth_choice == "Register":
        ru_user = st.sidebar.text_input("Choose username", key="ru_user")
        ru_pass = st.sidebar.text_input("Choose password", type="password", key="ru_pass")
        if st.sidebar.button("Register"):
            if not ru_user.strip() or not ru_pass:
                st.sidebar.error("Enter username and password.")
            else:
                ok, msg = create_user(ru_user.strip(), ru_pass)
                if ok:
                    st.sidebar.success(msg + " You can now login.")
                else:
                    st.sidebar.error(msg)
    else:  # Guest
        if st.sidebar.button("Start as Guest"):
            # create a unique guest id for the session (not persisted)
            st.session_state.logged_in = True
            st.session_state.username = f"guest_{uuid.uuid4().hex[:8]}"
            st.session_state.guest = True
            st.session_state.guest_cards = []
            st.sidebar.info("Guest mode: cards are local to this browser session and will not be saved persistently.")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        logout()

# If not logged in yet, show a friendly message
if not st.session_state.logged_in:
    st.info("Please Login or Register from the sidebar, or use Guest mode to try the app (no persistent save).")
    st.stop()

# ---------------- Main menu for logged in users ----------------
menu = st.sidebar.radio("Menu", ["Your Credit Cards", "Add New Credit Card", "Delete Credit Card", "Export My Cards"])

user_cards = get_current_user_cards()

# ---- YOUR CARDS ----
if menu == "Your Credit Cards":
    st.header("📂 Your Saved Credit Cards")
    if not user_cards:
        st.info("📭 Empty Folder! Please add your credit card (use 'Add New Credit Card').")
    else:
        # Search & filter
        q = st.text_input("Search by owner name or last4 digits (leave blank for all)", "")
        filtered = []
        for c in user_cards:
            last4 = c.get("number","")[-4:]
            owner = c.get("owner_name","")
            if q.strip() == "" or q.lower() in owner.lower() or q in last4:
                filtered.append(c)

        # Sort option
        sort_by = st.selectbox("Sort by", ["Default", "Expiry (soonest first)", "Owner (A→Z)"])
        if sort_by == "Expiry (soonest first)":
            def exp_key(c):
                try:
                    return (int(c["year"]), int(c["month"]))
                except:
                    return (9999, 99)
            filtered.sort(key=exp_key)
        elif sort_by == "Owner (A→Z)":
            filtered.sort(key=lambda x: x.get("owner_name","").lower())

        cols = st.columns(2)
        for idx, card in enumerate(filtered):
            card_type, logo_url = get_card_type_and_logo(card.get("number",""))
            masked = "**** **** **** " + (card.get("number","")[-4:] if card.get("number") else "----")
            status = check_expiry(card.get("month","--"), card.get("year","----"))
            if status == "Expired":
                color = "#FF4B4B"
            elif status == "Expiring Soon":
                color = "#FFA500"
            elif status == "InvalidDate":
                color = "#777777"
            else:
                color = "#2E8B57"

            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div style="background:{color};padding:18px;border-radius:12px;color:white;margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-weight:700;font-size:18px;">{card_type}</div>
                            <img src="{logo_url}" width="48">
                        </div>
                        <div style="margin-top:8px;font-size:16px;"><b>{masked}</b></div>
                        <div style="margin-top:6px;">Owner: {card.get('owner_name','Unnamed')}</div>
                        <div>Expiry: {card.get('month','--')}/{card.get('year','----')}</div>
                        <div>Status: <b>{status}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Two actions: See Full Details, Validation Check
                dcol, vcol = st.columns([1,1])
                # Find actual index in user_cards (for deletion or update)
                actual_index = user_cards.index(card)
                with dcol:
                    if st.button(f"🔍 See Full Details ({card.get('owner_name','')})", key=f"details_{actual_index}_{st.session_state.username}"):
                        st.info(
                            f"**Full Details**\n\n"
                            f"👤 Owner: {card.get('owner_name','')}\n\n"
                            f"💳 Number: {card.get('number','')}\n\n"
                            f"📅 Expiry: {card.get('month','')}/{card.get('year','')}\n\n"
                            f"🔒 CVV: {card.get('cvv','')}\n"
                        )
                with vcol:
                    if st.button(f"✅ Validation Check ({card.get('owner_name','')})", key=f"validate_{actual_index}_{st.session_state.username}"):
                        num = card.get("number","").replace(" ","").replace("-","")
                        # Ask for current date override
                        cm = st.text_input("Current Month (MM)", value=str(datetime.now().month), key=f"curm_{actual_index}_{st.session_state.username}")
                        cy = st.text_input("Current Year (YYYY)", value=str(datetime.now().year), key=f"cury_{actual_index}_{st.session_state.username}")
                        # Simple validation
                        if not (num.isdigit() and len(num) in [13,15,16]):
                            st.error("❌ Invalid stored card number format")
                        elif not luhn_check(num):
                            st.error("❌ Invalid credit card number (failed Luhn check)")
                        elif not (cm.isdigit() and 1 <= int(cm) <= 12 and cy.isdigit() and len(cy) == 4):
                            st.error("❌ Enter a valid current month/year to validate")
                        else:
                            # use provided current month/year to check expiry
                            if int(card.get("year")) < int(cy) or (int(card.get("year")) == int(cy) and int(card.get("month")) < int(cm)):
                                st.warning("❌ Card has expired")
                            else:
                                st.success(f"✅ Card is valid! Type: {card_type}")

        st.markdown("---")

# ---- ADD NEW CARD ----
elif menu == "Add New Credit Card":
    st.header("➕ Add New Credit Card")
    st.markdown("Add a label (owner name) so you can identify the card easily.")
    owner_name = st.text_input("Owner / Label (e.g., 'Upal - Personal')")
    card_number = st.text_input("Credit Card Number (spaces/dashes allowed)").replace(" ", "").replace("-", "")
    month = st.text_input("Expiration Month (MM)")
    year = st.text_input("Expiration Year (YYYY)")
    cvv = st.text_input("CVV", type="password")

    if st.button("💾 Save Card"):
        # validations
        if not owner_name.strip():
            st.error("Enter an owner / label for the card.")
        elif not (card_number.isdigit() and len(card_number) in [13,15,16]):
            st.error("Invalid card number format (digits only after stripping).")
        elif not luhn_check(card_number):
            st.error("Invalid credit card number (failed Luhn check).")
        elif not (month.isdigit() and 1 <= int(month) <= 12):
            st.error("Invalid expiration month (MM).")
        elif not (year.isdigit() and len(year) == 4):
            st.error("Invalid expiration year (YYYY).")
        elif not (cvv.isdigit() and len(cvv) in [3,4]):
            st.error("Invalid CVV.")
        else:
            new_card = {
                "owner_name": owner_name.strip(),
                "number": card_number,
                "month": month,
                "year": year,
                "cvv": cvv
            }
            cards = get_current_user_cards()
            cards.append(new_card)
            save_current_user_cards(cards)
            st.success(f"Saved {new_card['owner_name']} • ****{new_card['number'][-4:]}")
            st.balloons()

# ---- DELETE CARD ----
elif menu == "Delete Credit Card":
    st.header("🗑️ Delete Credit Card")
    cards = get_current_user_cards()
    if not cards:
        st.info("No saved cards.")
    else:
        options = [f"{c.get('owner_name','Unnamed')} • ****{c.get('number','')[-4:]}" for c in cards]
        choice = st.selectbox("Select card to delete", ["-- select --"] + options)
        if choice != "-- select --":
            idx = options.index(choice)
            if st.button("❌ Delete Selected Card"):
                deleted = cards.pop(idx)
                save_current_user_cards(cards)
                st.success(f"Deleted {deleted.get('owner_name','Unnamed')} • ****{deleted.get('number','')[-4:]}")

# ---- EXPORT ----
elif menu == "Export My Cards":
    st.header("📤 Export My Cards (JSON)")
    cards = get_current_user_cards()
    st.markdown("Download a JSON backup of your cards stored in this app (for your account only).")
    if not cards:
        st.info("No cards to export.")
    else:
        payload = json.dumps(cards, indent=4)
        st.download_button("⬇️ Download JSON", payload, file_name=f"{st.session_state.username}_cards.json", mime="application/json")

# footer / security note
st.markdown("---")
st.markdown(
    "<small>⚠️ Security note: This demo stores card data locally in <code>data.json</code> (or in-session for Guest). "
    "It is <b>not</b> suitable for storing real card data in production. For production use, implement secure authentication, encrypt stored data, "
    "and follow PCI guidelines.</small>", unsafe_allow_html=True
)



