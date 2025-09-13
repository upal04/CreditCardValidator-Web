# app.py
# Simple, reliable Credit Card Manager (Streamlit)
# - Login / Register
# - Add card, View cards (masked)
# - Per-card actions: Show Full Details, Check Validity, Delete (single click, no double-click bug)
# - Delete Account (with confirmation)
#
# Data stored in users.json in the same folder.
# This file is intentionally simple and well-commented for beginners.

import streamlit as st
import json
import os
import uuid
from datetime import datetime

USERS_FILE = "users.json"


# -------------------------
# Simple persistent storage
# -------------------------
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# -------------------------
# Card validation helpers
# -------------------------
def luhn_check(number: str) -> bool:
    """Return True if number passes the Luhn algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 12:  # too short to be valid
        return False
    checksum = 0
    digits = digits[::-1]
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def expiry_status(expiry: str) -> str:
    """
    expiry expected "MM/YY" or "MM/YYYY".
    Return:
      - "Invalid Format"
      - "Expired"
      - "OK"
    """
    try:
        parts = expiry.split("/")
        if len(parts) != 2:
            return "Invalid Format"
        mm = int(parts[0])
        yy = int(parts[1])
        if yy < 100:  # assume YY
            yy = 2000 + yy
        # create last day of expiry month as check date
        expiry_date = datetime(yy, mm, 1)
        # treat expiry as valid through the month (compare using month resolution)
        now = datetime.now()
        if (yy, mm) < (now.year, now.month):
            return "Expired"
        return "OK"
    except Exception:
        return "Invalid Format"


def card_validity(number: str, expiry: str) -> str:
    """Return a human status: '✅ Valid', '❌ Invalid Number', '❌ Expired', '❌ Invalid Expiry'"""
    if not luhn_check(number):
        return "❌ Invalid Number"
    exp = expiry_status(expiry)
    if exp == "Invalid Format":
        return "❌ Invalid Expiry Format"
    if exp == "Expired":
        return "❌ Expired"
    return "✅ Valid"


# -------------------------
# Small helpers
# -------------------------
def mask_pan(number: str) -> str:
    digits = "".join([d for d in number if d.isdigit()])
    if len(digits) <= 4:
        return digits
    return "**** **** **** " + digits[-4:]


# -------------------------
# Session-state bootstrap
# -------------------------
st.set_page_config(page_title="Card Manager", layout="centered")
if "users" not in st.session_state:
    st.session_state["users"] = load_users()  # persistent store (dict)
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
# transient UI flags stored here
if "show_details" not in st.session_state:
    st.session_state["show_details"] = None
if "validity_result" not in st.session_state:
    st.session_state["validity_result"] = None
if "message" not in st.session_state:
    st.session_state["message"] = None


# -------------------------
# Callbacks (used by on_click)
# -------------------------
def cb_show_details(card_id: str):
    # toggle showing details for this card
    if st.session_state.get("show_details") == card_id:
        st.session_state["show_details"] = None
    else:
        st.session_state["show_details"] = card_id
    # ensure any previous validity result is kept separate (not cleared)


def cb_check_validity(card_id: str):
    user = st.session_state["current_user"]
    if not user:
        return
    cards = st.session_state["users"].get(user, {}).get("cards", [])
    # find card by id
    for c in cards:
        if c["id"] == card_id:
            st.session_state["validity_result"] = {"id": card_id, "status": card_validity(c["number"], c["expiry"])}
            return


def cb_delete_card(card_id: str):
    user = st.session_state["current_user"]
    if not user:
        return
    cards = st.session_state["users"].get(user, {}).get("cards", [])
    new_cards = [c for c in cards if c["id"] != card_id]
    st.session_state["users"][user]["cards"] = new_cards
    save_users(st.session_state["users"])
    # clear any showing state for that card
    if st.session_state.get("show_details") == card_id:
        st.session_state["show_details"] = None
    if st.session_state.get("validity_result") and st.session_state["validity_result"]["id"] == card_id:
        st.session_state["validity_result"] = None
    st.session_state["message"] = "Card deleted."


# -------------------------
# Auth / Register functions
# -------------------------
def do_register(username: str, password: str) -> (bool, str):
    if not username or not password:
        return False, "Username and password cannot be empty."
    if username in st.session_state["users"]:
        return False, "Username already exists."
    # create user record
    st.session_state["users"][username] = {"password": password, "cards": []}
    save_users(st.session_state["users"])
    return True, "Account created. Please log in."


def do_login(username: str, password: str) -> (bool, str):
    users = st.session_state["users"]
    if username in users and users[username]["password"] == password:
        st.session_state["current_user"] = username
        # clear UI flags
        st.session_state["show_details"] = None
        st.session_state["validity_result"] = None
        st.session_state["message"] = None
        return True, "Logged in."
    return False, "Invalid username or password."


def do_logout():
    st.session_state["current_user"] = None
    st.session_state["show_details"] = None
    st.session_state["validity_result"] = None
    st.session_state["message"] = None


def do_delete_account(confirm: bool) -> (bool, str):
    user = st.session_state["current_user"]
    if not user:
        return False, "No user logged in."
    if not confirm:
        return False, "You must confirm account deletion."
    # remove user entirely
    st.session_state["users"].pop(user, None)
    save_users(st.session_state["users"])
    st.session_state["current_user"] = None
    return True, "Account deleted."


# -------------------------
# UI: Login / Register
# -------------------------
st.title("💳 Simple Card Manager")

if not st.session_state["current_user"]:
    st.write("Please login or register to continue.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login")
            if login_submit:
                ok, msg = do_login(username.strip(), password)
                if ok:
                    st.success(msg)
                    st.experimental_rerun()  # short reload to show dashboard
                else:
                    st.error(msg)

    with col2:
        st.subheader("Register")
        with st.form("register_form"):
            r_username = st.text_input("Choose username", key="reg_username")
            r_password = st.text_input("Choose password", type="password", key="reg_password")
            register_submit = st.form_submit_button("Register")
            if register_submit:
                ok, msg = do_register(r_username.strip(), r_password)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("---")
    st.caption("Note: Data stored locally in users.json (same folder as this script).")

# -------------------------
# UI: Dashboard
# -------------------------
else:
    user = st.session_state["current_user"]
    st.sidebar.success(f"Logged in: {user}")
    if st.sidebar.button("Logout"):
        do_logout()
        st.experimental_rerun()

    page = st.sidebar.radio("Menu", ["Add Card", "View Cards", "Delete Account"])

    # -------- Add Card --------
    if page == "Add Card":
        st.header("Add a new card (saved to your account)")
        with st.form("add_card_form"):
            holder = st.text_input("Cardholder name")
            number = st.text_input("Card number (digits only)")
            expiry = st.text_input("Expiry (MM/YY or MM/YYYY)")
            cvv = st.text_input("CVV", type="password")
            submit = st.form_submit_button("Save card")
            if submit:
                if not (holder and number and expiry and cvv):
                    st.error("All fields are required.")
                else:
                    # create card with unique id
                    card_id = uuid.uuid4().hex
                    card = {
                        "id": card_id,
                        "holder": holder,
                        "number": number,
                        "expiry": expiry,
                        "cvv": cvv,
                        "created": datetime.now().isoformat()
                    }
                    st.session_state["users"].setdefault(user, {"password": st.session_state["users"][user]["password"], "cards": []})
                    st.session_state["users"][user]["cards"].append(card)
                    save_users(st.session_state["users"])
                    st.success("Card saved.")
                    # clear any UI flags and show nothing else
                    st.session_state["show_details"] = None
                    st.session_state["validity_result"] = None
                    st.experimental_rerun()

    # -------- View Cards --------
    elif page == "View Cards":
        st.header("Your saved cards")
        cards = st.session_state["users"].get(user, {}).get("cards", [])
        if not cards:
            st.info("No cards saved yet.")
        else:
            # show the list; each card gets stable unique buttons via on_click and unique keys
            for card in list(cards):  # iterate over copy to be safe if deleted
                cid = card["id"]
                st.subheader(card["holder"])
                st.write("Number:", mask_pan(card["number"]))
                st.write("Expiry:", card["expiry"])
                st.write("Added:", card.get("created", ""))

                # three columns of actions
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    st.button(
                        "Show Full Details",
                        key=f"details_{cid}",
                        on_click=cb_show_details,
                        args=(cid,),
                    )
                with c2:
                    st.button(
                        "Check Validity",
                        key=f"validity_{cid}",
                        on_click=cb_check_validity,
                        args=(cid,),
                    )
                with c3:
                    st.button(
                        "Delete Card",
                        key=f"delete_{cid}",
                        on_click=cb_delete_card,
                        args=(cid,),
                    )

                # If the user asked to see details for this card, show them
                if st.session_state.get("show_details") == cid:
                    st.info(
                        f"**Full details**\n\nHolder: {card['holder']}\n\nNumber: {card['number']}\n\nExpiry: {card['expiry']}\n\nCVV: {card['cvv']}"
                    )

                # If the user checked validity for this card, show the result
                vr = st.session_state.get("validity_result")
                if vr and vr.get("id") == cid:
                    st.write("**Validity:**", vr.get("status"))

                st.markdown("---")

            # show any global message (like deletion)
            if st.session_state.get("message"):
                st.success(st.session_state["message"])
                st.session_state["message"] = None

    # -------- Delete Account --------
    elif page == "Delete Account":
        st.header("Delete your account (permanent)")
        st.write("This will remove your account and all saved cards.")
        with st.form("delete_account_form"):
            confirm = st.checkbox("I confirm: delete my account and all saved cards")
            do_delete = st.form_submit_button("Delete my account")
            if do_delete:
                if not confirm:
                    st.error("You must check the confirmation box.")
                else:
                    ok, msg = do_delete_account(confirm=True)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)
