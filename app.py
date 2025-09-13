import streamlit as st
import datetime
import uuid

# Page configuration
st.set_page_config(
    page_title="💳 Credit Card Manager", 
    page_icon="💳", 
    layout="centered"
)

# -------------------------
# Session State Initialization
# -------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# -------------------------
# Helper Functions
# -------------------------
def format_card_number(number):
    """Format card number as XXXX XXXX XXXX XXXX"""
    clean_number = number.replace(" ", "").replace("-", "")
    return " ".join([clean_number[i:i+4] for i in range(0, len(clean_number), 4)])

def mask_card_number(number):
    """Show only last 4 digits of card number"""
    clean_number = number.replace(" ", "").replace("-", "")
    return "**** **** **** " + clean_number[-4:]

def is_card_valid(expiry_date):
    """Check if a card is not expired (MM/YY format)"""
    try:
        month, year = expiry_date.split("/")
        month, year = int(month), int(year)
        
        # Convert two-digit year to four-digit
        if year < 100:
            year += 2000
            
        today = datetime.date.today()
        return (year > today.year) or (year == today.year and month >= today.month)
    except:
        return False

def login_user(username, password):
    """Authenticate user login"""
    users = st.session_state.users
    return username in users and users[username]["password"] == password

def register_user(username, password):
    """Register a new user"""
    if username in st.session_state.users:
        return False
        
    st.session_state.users[username] = {
        "password": password,
        "cards": []
    }
    return True

# -------------------------
# UI Components
# -------------------------
def show_login_form():
    """Display login form"""
    st.subheader("🔑 Login to your account")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    
    if st.button("Login", type="primary"):
        if login_user(username.strip(), password):
            st.session_state.current_user = username
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

def show_registration_form():
    """Display registration form"""
    st.subheader("📝 Create a new account")
    new_user = st.text_input("Choose Username", key="reg_user")
    new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
    
    if st.button("Register"):
        if not new_user.strip() or not new_pass.strip():
            st.warning("Username and password cannot be empty!")
        elif register_user(new_user.strip(), new_pass):
            st.success("Account created! You can login now.")
        else:
            st.error("Username already exists.")

def show_add_card_form():
    """Display form to add a new card"""
    st.subheader("➕ Add a New Card")
    
    with st.form("add_card_form"):
        holder = st.text_input("Cardholder Name")
        number = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
        expiry = st.text_input("Expiry Date", placeholder="MM/YY")
        cvv = st.text_input("CVV", type="password")
        
        if st.form_submit_button("Save Card", type="primary"):
            # Clean the card number
            clean_number = number.replace(" ", "").replace("-", "")
            
            # Validate inputs
            if not all([holder, clean_number, expiry, cvv]):
                st.warning("All fields are required.")
            elif not clean_number.isdigit() or len(clean_number) != 16:
                st.error("Card number must be 16 digits.")
            elif not cvv.isdigit() or len(cvv) != 3:
                st.error("CVV must be 3 digits.")
            else:
                # Save the card
                card = {
                    "id": uuid.uuid4().hex,
                    "holder": holder,
                    "number": clean_number,
                    "expiry": expiry,
                    "cvv": cvv,
                }
                st.session_state.users[st.session_state.current_user]["cards"].append(card)
                st.success("Card saved successfully!")

def show_saved_cards():
    """Display all saved cards"""
    st.subheader("📂 Your Saved Cards")
    user_cards = st.session_state.users[st.session_state.current_user]["cards"]
    
    if not user_cards:
        st.info("No cards saved yet. Add your first card above!")
        return
        
    for i, card in enumerate(user_cards):
        with st.expander(f"💳 Card {i+1}: {mask_card_number(card['number'])}", expanded=False):
            st.write(f"**Cardholder:** {card['holder']}")
            st.write(f"**Expiry:** {card['expiry']}")
            
            # Create columns for action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ Show Details", key=f"details_{card['id']}"):
                    st.info(
                        f"**Cardholder:** {card['holder']}\n\n"
                        f"**Number:** {format_card_number(card['number'])}\n\n"
                        f"**Expiry:** {card['expiry']}\n\n"
                        f"**CVV:** {card['cvv']}"
                    )
            
            with col2:
                if st.button("✅ Check Validity", key=f"validity_{card['id']}"):
                    if is_card_valid(card['expiry']):
                        st.success("Card is valid")
                    else:
                        st.error("Card has expired!")
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{card['id']}"):
                    st.session_state.users[st.session_state.current_user]["cards"].remove(card)
                    st.success("Card deleted")
                    st.rerun()

def show_account_deletion():
    """Display account deletion options"""
    st.subheader("⚠️ Delete Account")
    st.warning("This action cannot be undone. All your cards will be permanently deleted.")
    
    if st.checkbox("I understand and want to delete my account"):
        if st.button("Delete My Account", type="primary"):
            # Remove user account
            del st.session_state.users[st.session_state.current_user]
            st.session_state.current_user = None
            st.success("Your account has been deleted.")
            st.rerun()

def show_logout():
    """Handle user logout"""
    st.session_state.current_user = None
    st.success("You have been logged out.")
    st.rerun()

# -------------------------
# Main Application
# -------------------------
st.markdown(
    "<h1 style='text-align:center;color:#1E90FF;'>💳 Credit Card Manager</h1>",
    unsafe_allow_html=True,
)

# Check if user is logged in
if not st.session_state.current_user:
    # Show authentication options
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        show_login_form()
    
    with auth_tab2:
        show_registration_form()
else:
    # User is logged in - show dashboard
    user = st.session_state.current_user
    st.sidebar.success(f"👤 Logged in as {user}")
    
    # Navigation menu
    menu_options = {
        "Add Card": show_add_card_form,
        "View Cards": show_saved_cards,
        "Delete Account": show_account_deletion,
        "Logout": show_logout
    }
    
    selected_menu = st.sidebar.radio("📌 Menu", list(menu_options.keys()))
    
    # Display selected section
    menu_options[selected_menu]()
    
    # Show card count in sidebar
    card_count = len(st.session_state.users[user]["cards"])
    st.sidebar.info(f"📊 You have {card_count} saved card(s)")
