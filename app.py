import streamlit as st
import json
import os
from datetime import datetime

# File for saving card data
CARD_FILE = "cards.json"

# Load cards
def load_cards():
    if os.path.exists(CARD_FILE):
        with open(CARD_FILE, "r") as f:
            return json.load(f)
    return []

# Save cards
def save_cards(cards):
    with open(CARD_FILE, "w") as f:
        json.dump(cards, f, indent=4)

# Luhn Algorithm
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

# Detect card type
def get_card_type(number):
    if number.startswith("4"):
        return "Visa"
    elif number.startswith(("51", "52", "53", "54", "55")):
        return "MasterCard"
    elif number.startswith(("34", "37")):
        return "American Express"
    elif number.startswith("6"):
        return "Discover"
    else:
        return "Unknown"

# Expiry check
def check_expiry(month, year):
    now = datetime.now()
    exp_date = datetime(int(year), int(month), 1)
    if exp_date < now:
        return "Expired"
    months_left = (exp_date.year - now.year) * 12 + (exp_date.month - now.month)
    if months_left <= 3:
        return "Expiring Soon"
    return "Valid"

# UI
st.set_page_config(page_title="💳 Credit Card Manager", layout="centered")
st.title("💳 Credit Card Manager")

menu = ["📂 Your Credit Cards", "➕ Add New Credit Card", "❌ Delete Credit Card"]
choice = st.sidebar.radio("Menu", menu)

cards = load_cards()

# ---- Your Credit Cards ----
if choice == "📂 Your Credit Cards":
    st.header("📂 Your Saved Credit Cards")
    if not cards:
        st.info("📭 Empty Folder! Please add your credit card.")
    else:
        cols = st.columns(2)
        for idx, card in enumerate(cards):
            with cols[idx % 2]:
                card_type = get_card_type(card["number"])
                masked_number = "**** **** **** " + card["number"][-4:]
                status = check_expiry(card["month"], card["year"])

                # Card color based on status
                if status == "Expired":
                    color = "#FF4B4B"
                elif status == "Expiring Soon":
                    color = "#FFA500"
                else:
                    color = "#4CAF50"

                st.markdown(
                    f"""
                    <div style="background:{color};padding:20px;border-radius:15px;color:white;margin-bottom:15px;">
                        <h3>{card_type}</h3>
                        <p><b>{masked_number}</b></p>
                        <p>Owner: {card["name"]}</p>
                        <p>Expiry: {card["month"]}/{card["year"]}</p>
                        <p>Status: <b>{status}</b></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---- Add New Card ----
elif choice == "➕ Add New Credit Card":
    st.header("➕ Add New Credit Card")
    name = st.text_input("Card Holder Name")
    number = st.text_input("Credit Card Number").replace(" ", "").replace("-", "")
    month = st.text_input("Expiration Month (MM)")
    year = st.text_input("Expiration Year (YYYY)")
    cvv = st.text_input("CVV", type="password")

    if st.button("Save Card"):
        if not name.strip():
            st.error("Please enter card holder name")
        elif not (number.isdigit() and len(number) in [13, 15, 16]):
            st.error("Invalid card number format")
        elif not luhn_check(number):
            st.error("Invalid credit card number (failed Luhn check)")
        elif not (month.isdigit() and 1 <= int(month) <= 12):
            st.error("Invalid expiration month")
        elif not (year.isdigit() and len(year) == 4):
            st.error("Invalid expiration year")
        elif not (cvv.isdigit() and len(cvv) in [3, 4]):
            st.error("Invalid CVV")
        else:
            cards.append({"name": name, "number": number, "month": month, "year": year, "cvv": cvv})
            save_cards(cards)
            st.success("✅ Card saved successfully!")

# ---- Delete Card ----
elif choice == "❌ Delete Credit Card":
    st.header("❌ Delete Credit Card")
    if not cards:
        st.info("No cards to delete.")
    else:
        options = [f"{c['name']} - ****{c['number'][-4:]}" for c in cards]
        to_delete = st.selectbox("Select a card to delete", options)
        if st.button("Delete"):
            index = options.index(to_delete)
            deleted_card = cards.pop(index)
            save_cards(cards)
            st.warning(f"❌ Deleted card of {deleted_card['name']} ({deleted_card['number'][-4:]})")
