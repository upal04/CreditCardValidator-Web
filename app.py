import streamlit as st
import json
import os

# ---------- Config ----------
FILE = "cards.json"

# ---------- Storage helpers ----------
def load_cards():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_cards(cards):
    with open(FILE, "w") as f:
        json.dump(cards, f, indent=4)

# ---------- Luhn Algorithm ----------
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

# ---------- Card Type ----------
def get_card_type(number):
    if number.startswith("4"):
        return "Visa"
    elif number.startswith(("51","52","53","54","55")):
        return "MasterCard"
    elif number.startswith(("34","37")):
        return "American Express"
    elif number.startswith("6"):
        return "Discover"
    else:
        return "Unknown"

# ---------- UI ----------
st.set_page_config(page_title="Credit Card Manager", page_icon="💳", layout="centered")
st.title("💳 Credit Card Manager")

st.markdown(
    """
    <style>
    .main { background-color: #f6f9fc; }
    .card-title { font-size:20px; font-weight:700; color:#0b5394; }
    .muted { color: #556; }
    .small { font-size:12px; color:#666; }
    </style>
    """,
    unsafe_allow_html=True
)

menu = st.sidebar.radio("📂 Menu", ["Your Credit Cards", "Add New Credit Card", "Delete Credit Card"])
cards = load_cards()

# ----- Option 1: Your Credit Cards -----
if menu == "Your Credit Cards":
    st.header("📁 Your Saved Credit Cards")
    if not cards:
        st.info("📭 Empty Folder! Please add your credit card (use 'Add New Credit Card').")
    else:
        for i, card in enumerate(cards):
            owner = card.get("owner_name", "Unnamed")
            ctype = card.get("type", get_card_type(card.get("number","")))
            last4 = card.get("number","")[-4:] if card.get("number") else "----"
            exp = f"{card.get('month','--')}/{card.get('year','----')}"
            # Main row
            with st.expander(f"💳 {ctype} • {owner} • ****{last4}", expanded=False):
                st.markdown(f"**Owner / Label:** {owner}")
                st.markdown(f"**Card Type:** {ctype}")
                st.markdown(f"**Last 4 digits:** ****{last4}")
                st.markdown(f"**Expiry:** {exp}")
                if st.checkbox(f"Show full number & CVV (card #{i+1})", key=f"show_{i}"):
                    st.code(f"Full Number: {card.get('number','')}")
                    st.code(f"CVV: {card.get('cvv','')}")
                action = st.radio("Choose action", ["See Full Details", "Validation Check"], key=f"action_{i}")
                if action == "See Full Details":
                    st.write("**Full details:**")
                    st.write(f"- Number: {card.get('number','')}")
                    st.write(f"- CVV: {card.get('cvv','')}")
                    st.write(f"- Expiry: {card.get('month','')}/{card.get('year','')}")
                    st.write(f"- Owner: {owner}")
                elif action == "Validation Check":
                    # For validation check we may want the current month/year - allow override
                    c_month = st.text_input("Current Month (MM)", value=card.get("current_month",""), key=f"curm_{i}", max_chars=2)
                    c_year = st.text_input("Current Year (YYYY)", value=card.get("current_year",""), key=f"cury_{i}", max_chars=4)
                    if st.button("Run Validation", key=f"validate_{i}"):
                        num = card.get("number","").replace(" ","").replace("-","")
                        if not (num.isdigit() and len(num) in [13,15,16]):
                            st.error("❌ Invalid card number format (stored)")
                        elif not luhn_check(num):
                            st.error("❌ Invalid card number (failed Luhn check)")
                        elif not (c_month.isdigit() and 1 <= int(c_month) <= 12):
                            st.error("❌ Enter a valid current month (MM)")
                        elif not (c_year.isdigit() and len(c_year) == 4):
                            st.error("❌ Enter a valid current year (YYYY)")
                        else:
                            if int(card.get("year")) < int(c_year) or (int(card.get("year")) == int(c_year) and int(card.get("month")) < int(c_month)):
                                st.warning("❌ Card has expired")
                            else:
                                st.success(f"✅ Valid Card! Type: {ctype}")

# ----- Option 2: Add New Credit Card -----
elif menu == "Add New Credit Card":
    st.header("➕ Add New Credit Card")
    st.markdown("Add a friendly owner/label so you can quickly identify the card later (e.g., 'Upal - Personal').")
    owner_name = st.text_input("Owner / Card Label (e.g., 'John - Personal')")
    card_number = st.text_input("Credit Card Number (spaces/dashes allowed)").replace(" ", "").replace("-", "")
    month = st.text_input("Expiration Month (MM)")
    year = st.text_input("Expiration Year (YYYY)")
    cvv = st.text_input("CVV", type="password")
    current_month = st.text_input("Current Month (MM)")
    current_year = st.text_input("Current Year (YYYY)")

    if st.button("💾 Save Card"):
        # Validations
        if not owner_name.strip():
            st.error("❌ Please enter an owner name / label for this card.")
        elif not (card_number.isdigit() and len(card_number) in [13, 15, 16]):
            st.error("❌ Invalid card number format")
        elif not luhn_check(card_number):
            st.error("❌ Invalid credit card number (failed Luhn check)")
        elif not (month.isdigit() and 1 <= int(month) <= 12):
            st.error("❌ Invalid expiration month")
        elif not (year.isdigit() and len(year) == 4):
            st.error("❌ Invalid expiration year")
        elif not (cvv.isdigit() and len(cvv) in [3,4]):
            st.error("❌ Invalid CVV")
        elif not (current_month.isdigit() and current_year.isdigit()):
            st.error("❌ Enter valid current month and year")
        else:
            card = {
                "owner_name": owner_name.strip(),
                "number": card_number,
                "month": month,
                "year": year,
                "cvv": cvv,
                "current_month": current_month,
                "current_year": current_year,
                "type": get_card_type(card_number)
            }
            cards.append(card)
            save_cards(cards)
            st.success(f"✅ Saved {card['type']} • {card['owner_name']} • ****{card['number'][-4:]}")
            st.balloons()

# ----- Option 3: Delete Credit Card -----
elif menu == "Delete Credit Card":
    st.header("🗑️ Delete Credit Card")
    if not cards:
        st.info("No saved cards to delete.")
    else:
        card_list = [f"{c.get('owner_name','Unnamed')} • {c.get('type',get_card_type(c.get('number','')))} • ****{c.get('number','')[-4:]}" for c in cards]
        choice = st.selectbox("Select a card to delete", ["-- select --"] + card_list)
        if choice != "-- select --":
            idx = card_list.index(choice)
            if st.button("❌ Delete Selected Card"):
                deleted = cards.pop(idx)
                save_cards(cards)
                st.success(f"Deleted {deleted.get('owner_name','Unnamed')} • ****{deleted.get('number','')[-4:]}")

# ---------- small footer ----------
st.markdown("---")
st.markdown("<div class='small muted'>⚠️ Demo / learning app: cards are stored locally in <code>cards.json</code> as plain text. Do NOT store real card CVVs or sensitive data here for production use.</div>", unsafe_allow_html=True)
