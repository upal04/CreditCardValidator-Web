# Import libraries we need
import streamlit as st  # For the web app interface
import datetime  # For date checks (like card expiry)
import uuid  # For unique card IDs
import mysql.connector  # For connecting to MySQL database
import os  # For environment variables
import re  # For password checks

# Database connection setup
# This gets the database URL from Railway (you set it in the app variables)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Function to connect to the database
def get_db_connection():
    # Parse the URL to get connection details
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    return mysql.connector.connect(
        host=url.hostname,  # Database server address
        user=url.username,  # Your username
        password=url.password,  # Your password
        database=url.path[1:],  # Database name (remove the /)
        port=url.port  # Port number
    )

# Function to create tables if they don't exist
def init_db():
    conn = get_db_connection()  # Connect to DB
    cursor = conn.cursor()  # Create a tool to run SQL commands
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(255) PRIMARY KEY,  # Unique username
            password VARCHAR(255) NOT NULL  # Password
        )
    ''')
    # Create cards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id VARCHAR(255) PRIMARY KEY,  # Unique card ID
            username VARCHAR(255) NOT NULL,  # Links to user
            holder VARCHAR(255) NOT NULL,  # Cardholder name
            number VARCHAR(255) NOT NULL,  # Card number
            expiry VARCHAR(255) NOT NULL,  # Expiry date
            cvv VARCHAR(255) NOT NULL,  # CVV
            FOREIGN KEY (username) REFERENCES users (username)  # Link to users
        )
    ''')
    conn.commit()  # Save changes
    cursor.close()  # Close tools
    conn.close()  # Close connection

# Function to load all users and cards from DB
def load_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get all users
    cursor.execute("SELECT username, password FROM users")
    users = {row[0]: {"password": row[1], "cards": []} for row in cursor.fetchall()}
    # Get all cards and add to users
    cursor.execute("SELECT id, username, holder, number, expiry, cvv FROM cards")
    for row in cursor.fetchall():
        card = {
            "id": row[0],
            "holder": row[2],  # Cardholder name
            "number": row[3],  # Card number
            "expiry": row[4],  # Expiry
            "cvv": row[5]  # CVV
        }
        users[row[1]]["cards"].append(card)  # Add card to the user
    cursor.close()
    conn.close()
    return users

# Function to save a new user
def save_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    cursor.close()
    conn.close()

# Function to save a new card
def save_card(username, card):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cards (id, username, holder, number, expiry, cvv) VALUES (%s, %s, %s, %s, %s, %s)",
                   (card["id"], username, card["holder"], card["number"], card["expiry"], card["cvv"]))
    conn.commit()
    cursor.close()
    conn.close()

# Function to delete a user and their cards
def delete_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE username = %s", (username,))  # Delete cards first
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))  # Then user
    conn.commit()
    cursor.close()
    conn.close()

# Function to delete a specific card
def delete_card(card_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = %s", (card_id,))
    conn.commit()
    cursor.close()
    conn.close()

# Helper function: Format card number (add spaces)
def format_number(number):
    return " ".join([number[i:i+4] for i in range(0, len(number), 4)])

# Helper function: Check if card is expired
def validate_card(expiry):
    try:
        mm, yy = expiry.split("/")  # Split MM/YY
        mm, yy = int(mm), int(yy)
        if yy < 100:  # If year is 24, make it 2024
            yy += 2000
        today = datetime.date.today()  # Today's date
        return (yy > today.year) or (yy == today.year and mm >= today.month)  # Future date?
    except:
        return False  # Invalid format

# Helper function: Hide card number (show last 4 digits)
def mask_number(number):
    return "**** **** **** " + number[-4:]

# Helper function: Check if password is strong
def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):  # Uppercase letter?
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):  # Lowercase letter?
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):  # Number?
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special character?
        return False, "Password must contain at least one special character (e.g., !@#$%^&*)."
    return True, "Password is strong."

# Helper function: Check if card number is valid (Luhn algorithm)
def validate_credit_card_number(number):
    if not number.isdigit() or len(number) != 16:  # Must be 16 digits
        return False
    def luhn_checksum(card_num):  # Math check for validity
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]  # Every other digit
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0  # Divisible by 10?
    return luhn_checksum(int(number))

# Auth function: Check login
def login(username, password):
    users = st.session_state["users"]  # Get users from memory
    return username in users and users[username]["password"] == password  # Match?

# Auth function: Register new user
def register(username, password):
    if username in st.session_state["users"]:  # Username taken?
        return False, "Username already exists."
    is_strong, msg = validate_password_strength(password)  # Check password
    if not is_strong:
        return False, msg
    save_user(username, password)  # Save to DB
    st.session_state["users"][username] = {"password": password, "cards": []}  # Add to memory
    return True, "Account created successfully!"

# App setup
st.set_page_config(page_title="💳 Credit Card Manager", page_icon="💳", layout="centered")  # App title and icon

# Initialize DB and load data
init_db()  # Create tables if needed
if "users" not in st.session_state:  # Load users if not in memory
    st.session_state["users"] = load_users()
if "current_user" not in st.session_state:  # Track logged-in user
    st.session_state["current_user"] = None

# Main app title
st.markdown("<h1 style='text-align:center;color:#1E90FF;'>💳 Credit Card Manager</h1>", unsafe_allow_html=True)

# If not logged in, show login/register tabs
if not st.session_state["current_user"]:
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "⚙️ Settings"])

    with tab1:  # Login tab
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login(username.strip(), password):  # Check login
                st.session_state["current_user"] = username
                st.success(f"Welcome back, {username}!")
                st.rerun()  # Refresh page
            else:
                st.error("Invalid username or password.")

    with tab2:  # Register tab
        st.subheader("Create a new account")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register"):
            if not new_user.strip() or not new_pass.strip():
                st.warning("Username and password cannot be empty!")
            else:
                success, msg = register(new_user.strip(), new_pass)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab3:  # Developer settings
        st.subheader("👨‍💻 Developer Dashboard")
        dev_key = st.text_input("🔑 Enter Developer Key", type="password")
        if dev_key == "upal140404":  # Secret key
            st.success("✅ Developer mode enabled")
            users_data = st.session_state["users"]
            st.info(f"📊 Total Accounts: {len(users_data)}")
            st.write("### 📋 Accounts Summary")
            for uname, details in users_data.items():
                st.write(f"- **{uname}** → {len(details['cards'])} card(s)")
            st.write("---")
            for uname, details in users_data.items():
                with st.expander(f"👤 User: {uname}  |  Cards: {len(details['cards'])}"):
                    st.write("**Password (stored):**", details["password"])
                    st.write("**Total Cards:**", len(details["cards"]))
                    for i, card in enumerate(details["cards"], start=1):
                        st.write(f"--- Card {i} ---")
                        st.write("Holder:", card["holder"])
                        st.write("Number:", format_number(card["number"]))
                        st.write("Expiry:", card["expiry"])
                        st.write("CVV:", card["cvv"])

# If logged in, show dashboard
else:
    user = st.session_state["current_user"]
    st.sidebar.success(f"👤 Logged in as {user}")  # Sidebar info

    menu = st.sidebar.radio("📌 Menu", ["Add Card", "See Cards", "Delete Account", "Logout"])  # Menu options

    if menu == "Add Card":  # Add card section
        st.subheader("➕ Add a New Card")
        holder = st.text_input("Cardholder Name", placeholder="Upal Pramanik")
        number = st.text_input("Card Number", placeholder="1234 5678 9012 3456").replace(" ", "").replace("-", "")
        expiry = st.text_input("Expiry (MM/YY)", placeholder="04/24")
        cvv = st.text_input("CVV", type="password", placeholder="123")
        if st.button("Save Card"):
            if not (holder and number and expiry and cvv):  # Check all fields
                st.warning("All fields are required.")
            elif not validate_credit_card_number(number):  # Check card number
                st.error("Invalid card number. It must be a valid 16-digit credit card number.")
            elif not cvv.isdigit() or len(cvv) != 3:  # Check CVV
                st.error("CVV must be 3 digits.")
            else:
                card = {  # Create card data
                    "id": uuid.uuid4().hex,  # Unique ID
                    "holder": holder,
                    "number": number,
                    "expiry": expiry,
                    "cvv": cvv,
                }
                st.session_state["users"][user]["cards"].append(card)  # Add to memory
                save_card(user, card)  # Save to DB
                st.success("Card saved!")

    elif menu == "See Cards":  # View cards section
        st.subheader("📂 Your Saved Cards")
        cards = st.session_state["users"][user]["cards"]
        if not cards:
            st.info("No cards saved yet.")
        else:
            for i, card in enumerate(cards):  # Loop through cards
                with st.expander(f"💳 Card {i+1}: {mask_number(card['number'])}"):  # Hide number
                    st.write("**Holder:**", card["holder"])
                    st.write("**Expiry:**", card["expiry"])
                    col1, col2, col3 = st.columns(3)  # Three buttons
                    with col1:
                        if st.button("👁️ Show Details", key=f"details_{card['id']}"):
                            st.info(f"**Cardholder:** {card['holder']}\n\n**Number:** {format_number(card['number'])}\n\n**Expiry:** {card['expiry']}\n\n**CVV:** {card['cvv']}")
                    with col2:
                        if st.button("✅ Check Validity", key=f"validity_{card['id']}"):
                            if validate_card(card['expiry']):
                                st.success("Card is Valid!")
                            else:
                                st.error("Invalid Card: Your Credit Card has expired!")
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{card['id']}"):
                            st.session_state["users"][user]["cards"].remove(card)  # Remove from memory
                            delete_card(card['id'])  # Remove from DB
                            st.success("Card deleted")
                            st.rerun()  # Refresh

    elif menu == "Delete Account":  # Delete account section
        st.subheader("⚠️ Delete Account Permanently")
        st.warning("This action cannot be undone. All your cards will be permanently deleted.")
        if st.checkbox("I confirm to delete my account and all cards"):
            if st.button("Delete My Account"):
                delete_user(user)  # Delete from DB
                st.session_state["users"].pop(user, None)  # Remove from memory
                st.session_state["current_user"] = None  # Logout
                st.success("Your account has been deleted.")
                st.rerun()

    elif menu == "Logout":  # Logout section
        st.session_state["current_user"] = None  # Clear user
        st.success("You have been logged out.")
        st.rerun()

    # Show card count in sidebar
    card_count = len(st.session_state["users"][user]["cards"])
    st.sidebar.info(f"📊 You have {card_count} saved card(s)")
