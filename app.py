import streamlit as st
import datetime
import uuid

# Set up the page
st.set_page_config(
    page_title="💳 Credit Card Manager", 
    page_icon="💳", 
    layout="centered"
)

# Initialize session state for storing data
if "users" not in st.session_state:
    st.session_state.users = {}
    
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Helper functions
def format_card_number(number):
    """Format card number as XXXX XXXX XXXX XXXX"""
    # Remove any spaces or dashes
    clean_number = number.replace(" ", "").replace("-", "")
    # Add space every 4 characters
    return " ".join([clean_number[i:i+4] for i in range(0, len(clean_number), 4)])

def mask_card_number(number):
    """Show only last 4 digits of card number"""
    clean_number = number.replace(" ", "").replace("-", "")
    return "**** **** **** " + clean_number[-4:]

def check_card_expiry(expiry_date):
    """Check if a card is expired (MM/YY format)"""
    try:
        # Split the expiry date into month and year
        month, year = expiry_date.split("/")
        month = int(month)
        year = int(year)
        
        # Convert two-digit year to four-digit (e.g., 25 → 2025)
        if year < 100:
            year += 2000
            
        # Get today's date
        today = datetime.date.today()
        
        # Check if card is still valid
        if year > today.year:
            return True
        elif year == today.year and month >= today.month:
            return True
        else:
            return False
    except:
        return False

def login(username, password):
    """Check if username and password are correct"""
    users = st.session_state.users
    if username in users and users[username]["password"] == password:
        return True
    return False

def register(username, password):
    """Create a new user account"""
    if username in st.session_state.users:
        return False  # Username already exists
        
    st.session_state.users[username] = {
        "password": password,
        "cards": []  # Empty list for storing cards
    }
    return True

# Display the title
st.title("💳 Credit Card Manager")

# Check if user is logged in
if st.session_state.current_user is None:
    # Show login/register options
    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])
    
    with login_tab:
        st.header("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login(username, password):
                st.session_state.current_user = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with register_tab:
        st.header("Create New Account")
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        
        if st.button("Register"):
            if register(new_username, new_password):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists")

else:
    # User is logged in - show dashboard
    username = st.session_state.current_user
    user_data = st.session_state.users[username]
    
    st.sidebar.success(f"Logged in as: {username}")
    
    # Menu options
    menu_option = st.sidebar.radio(
        "Menu Options",
        ["Add Card", "View Cards", "Delete Account", "Logout"]
    )
    
    # Add a new card
    if menu_option == "Add Card":
        st.header("Add a New Credit Card")
        
        card_holder = st.text_input("Cardholder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date (MM/YY)")
        cvv = st.text_input("CVV", type="password")
        
        if st.button("Save Card"):
            # Validate inputs
            if not all([card_holder, card_number, expiry_date, cvv]):
                st.warning("Please fill in all fields")
            elif not card_number.replace(" ", "").replace("-", "").isdigit() or len(card_number.replace(" ", "").replace("-", "")) != 16:
                st.error("Card number must be 16 digits")
            elif not cvv.isdigit() or len(cvv) != 3:
                st.error("CVV must be 3 digits")
            else:
                # Create card dictionary
                new_card = {
                    "id": uuid.uuid4().hex,  # Unique ID for the card
                    "holder": card_holder,
                    "number": card_number.replace(" ", "").replace("-", ""),
                    "expiry": expiry_date,
                    "cvv": cvv
                }
                
                # Add card to user's collection
                user_data["cards"].append(new_card)
                st.success("Card saved successfully!")
    
    # View saved cards
    elif menu_option == "View Cards":
        st.header("Your Saved Cards")
        
        if not user_data["cards"]:
            st.info("You haven't saved any cards yet.")
        else:
            for index, card in enumerate(user_data["cards"]):
                # Display card in an expandable section
                with st.expander(f"Card {index+1}: {mask_card_number(card['number'])}"):
                    st.write(f"**Cardholder:** {card['holder']}")
                    st.write(f"**Expiry:** {card['expiry']}")
                    
                    # Create columns for buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Show Details", key=f"show_{card['id']}"):
                            st.write(f"**Full Number:** {format_card_number(card['number'])}")
                            st.write(f"**CVV:** {card['cvv']}")
                    
                    with col2:
                        if st.button("Check Validity", key=f"check_{card['id']}"):
                            if check_card_expiry(card['expiry']):
                                st.success("✅ Card is valid")
                            else:
                                st.error("❌ Card has expired")
                    
                    with col3:
                        if st.button("Delete", key=f"delete_{card['id']}"):
                            user_data["cards"].remove(card)
                            st.success("Card deleted")
                            st.rerun()
    
    # Delete account
    elif menu_option == "Delete Account":
        st.header("Delete Your Account")
        st.warning("This will permanently delete your account and all saved cards!")
        
        confirm = st.checkbox("I understand this action cannot be undone")
        if confirm and st.button("Delete My Account"):
            # Remove user from system
            del st.session_state.users[username]
            st.session_state.current_user = None
            st.success("Your account has been deleted")
            st.rerun()
    
    # Logout
    elif menu_option == "Logout":
        st.session_state.current_user = None
        st.success("You have been logged out")
        st.rerun()
