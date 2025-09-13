import streamlit as st

# ---------------- Luhn Algorithm ---------------- #
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

# ---------------- Card Type Detection ---------------- #
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

# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="Credit Card Validator", page_icon="💳", layout="centered")

st.markdown(
    """
    <style>
        .main {
            background-color: #f0f4f7;
        }
        .title {
            font-size: 36px;
            font-weight: bold;
            color: white;
            text-align: center;
            background: linear-gradient(90deg, #1ABC9C, #16A085);
            padding: 15px;
            border-radius: 12px;
        }
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #1ABC9C;
        }
        .stButton > button {
            background-color: #1ABC9C;
            color: white;
            font-size: 18px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 20px;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background-color: #16A085;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">💳 Credit Card Validator</div>', unsafe_allow_html=True)

st.markdown("### Please enter your credit card details below")

# ---------------- Input Fields ---------------- #
card_number = st.text_input("Credit Card Number (no spaces or dashes)").replace(" ", "").replace("-", "")
month = st.text_input("Expiration Month (MM)")
year = st.text_input("Expiration Year (YYYY)")
cvv = st.text_input("CVV", type="password")
current_month = st.text_input("Current Month (MM)")
current_year = st.text_input("Current Year (YYYY)")

# ---------------- Validate Button ---------------- #
if st.button("✅ Validate Card"):
    if not (card_number.isdigit() and len(card_number) in [13, 15, 16]):
        st.error("❌ Invalid card number format")
    elif not luhn_check(card_number):
        st.error("❌ Invalid credit card number (failed Luhn check)")
    elif not (month.isdigit() and 1 <= int(month) <= 12):
        st.error("❌ Invalid expiration month")
    elif not (year.isdigit() and len(year) == 4):
        st.error("❌ Invalid expiration year")
    elif not (cvv.isdigit() and len(cvv) in [3, 4]):
        st.error("❌ Invalid CVV")
    elif not (current_month.isdigit() and current_year.isdigit()):
        st.error("❌ Enter valid current month and year")
    else:
        if int(year) < int(current_year) or (int(year) == int(current_year) and int(month) < int(current_month)):
            st.warning("❌ Invalid Credit Card. Your card has expired!")
        else:
            st.success(f"✅ Your Credit Card is valid!\n\n💳 **Type:** {get_card_type(card_number)}")
