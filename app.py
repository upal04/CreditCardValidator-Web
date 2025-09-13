import streamlit as st

# ---------------------------
# Helper Functions
# ---------------------------
def luhn_check(card_number: str) -> bool:
    """Check if a credit card number is valid using the Luhn algorithm."""
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
    """Detect the type of credit card based on its prefix."""
    if number.startswith("4"):
        return "Visa"
    elif number.startswith(("51", "52", "53", "54", "55")):
        return "MasterCard"
    elif number.startswith(("34", "37")):
        return "American Express"
    elif number.startswith("6"):
        return "Discover"
    return "Unknown"


# ---------------------------
# Page Navigation with Session State
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_to(page_name: str):
    st.session_state.page = page_name


# ---------------------------
# Home Page
# ---------------------------
if st.session_state.page == "home":
    st.set_page_config(page_title="Credit Card Manager", page_icon="💳", layout="centered")

    st.title("💳 Credit Card Manager")
    st.subheader("Select an option to continue")

    if st.button("Validate Credit Card"):
        go_to("validator")


# ---------------------------
# Validator Page
# ---------------------------
elif st.session_state.page == "validator":
    st.title("💳 Credit Card Validator")
    st.write("Enter your card details below to check validity.")

    card_number = st.text_input("Credit Card Number")
    month = st.text_input("Expiration Month (MM)")
    year = st.text_input("Expiration Year (YYYY)")
    cvv = st.text_input("CVV", type="password")
    current_month = st.text_input("Current Month (MM)")
    current_year = st.text_input("Current Year (YYYY)")

    if st.button("✅ Validate"):
        # Validation checks
        if not (card_number.isdigit() and len(card_number) in [13, 15, 16]):
            st.error("Invalid card number format")
        elif not luhn_check(card_number):
            st.error("Invalid credit card number (failed Luhn check)")
        elif not (month.isdigit() and 1 <= int(month) <= 12):
            st.error("Invalid expiration month")
        elif not (year.isdigit() and len(year) == 4):
            st.error("Invalid expiration year")
        elif not (cvv.isdigit() and len(cvv) in [3, 4]):
            st.error("Invalid CVV")
        elif not (current_month.isdigit() and current_year.isdigit()):
            st.error("Enter valid current month and year")
        else:
            if int(year) < int(current_year) or (
                int(year) == int(current_year) and int(month) < int(current_month)
            ):
                st.warning("❌ Card has expired.")
            else:
                card_type = get_card_type(card_number)
                st.success(f"✅ Card is valid!\n**Type:** {card_type}")

    if st.button("⬅️ Back to Home"):
        go_to("home")
