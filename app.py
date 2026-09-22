import hashlib
import json
import os
import re
import secrets
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Car Prediction System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "car_details.csv"
USERS_FILE = "users.json"

# Demo seller details. Replace these later with your actual seller details.
SELLER_DETAILS = {
    "name": "Rajesh Kumar",
    "mobile": "9876543210",
    "whatsapp": "9876543210",
    "email": "rajesh@gmail.com",
    "location": "Panipat, Haryana",
}

# ---------------- DATA ----------------

@st.cache_data

def load_data():
    if not Path(DATA_FILE).exists():
        st.error(f"{DATA_FILE} not found. Keep it in the same folder as app.py.")
        st.stop()

    df = pd.read_csv(DATA_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    required = [
        "name",
        "year",
        "selling_price",
        "km_driven",
        "fuel",
        "seller_type",
        "transmission",
        "owner",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("Missing columns: " + ", ".join(missing))
        st.stop()

    for column in ["year", "selling_price", "km_driven"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in ["name", "fuel", "seller_type", "transmission", "owner"]:
        df[column] = df[column].astype(str).str.strip()

    return df.dropna(subset=required).reset_index(drop=True)


df = load_data()


def price(value):
    return f"₹{int(value):,}"


# ---------------- AUTHENTICATION ----------------

def hash_password(password: str, salt_hex: str | None = None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120_000,
    ).hex()
    return digest, salt.hex()


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)


def valid_email(email):
    return re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email) is not None


def create_user(username, email, password):
    users = load_users()
    key = username.strip().lower()
    if key in users:
        return False, "Username already exists."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."
    if not valid_email(email.strip()):
        return False, "Enter a valid email address."

    digest, salt = hash_password(password)
    users[key] = {
        "name": username.strip(),
        "email": email.strip().lower(),
        "password_hash": digest,
        "salt": salt,
    }
    save_users(users)
    return True, "Account created successfully. You can now log in."


def authenticate(username, password):
    users = load_users()
    key = username.strip().lower()
    user = users.get(key)
    if not user:
        return False, None

    digest, _ = hash_password(password, user["salt"])
    if secrets.compare_digest(digest, user["password_hash"]):
        return True, user
    return False, None


def reset_password(username, email, new_password):
    users = load_users()
    key = username.strip().lower()
    user = users.get(key)
    if not user:
        return False, "Account not found."
    if user.get("email", "").lower() != email.strip().lower():
        return False, "Username and email do not match."
    if len(new_password) < 6:
        return False, "New password must contain at least 6 characters."

    digest, salt = hash_password(new_password)
    user["password_hash"] = digest
    user["salt"] = salt
    users[key] = user
    save_users(users)
    return True, "Password reset successfully."


# ---------------- UI STYLING ----------------

st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #e8edf5 0%, #f4f6fa 48%, #e3eaf4 100%);
    color: #182230;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #152237 0%, #1d2d46 100%);
    border-right: 1px solid #223b5d;
}

[data-testid="stSidebar"] * {
    color: #edf4ff !important;
}

[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #b9c7d8 !important;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

.topbar {
    background: linear-gradient(120deg, #16243a, #274b72);
    border: 1px solid #385e87;
    border-radius: 18px;
    padding: 15px 20px;
    margin-bottom: 18px;
    box-shadow: 0 12px 28px rgba(24, 42, 68, .16);
}

.brand {
    font-size: 25px;
    font-weight: 900;
    color: #ffffff;
}

.brand-sub {
    color: #cbd8e7;
    font-size: 13px;
}

.auth-card {
    max-width: 650px;
    margin: 42px auto 18px auto;
    background: linear-gradient(145deg, #17263d, #253f60);
    border: 1px solid #3a5c82;
    border-radius: 26px;
    padding: 36px;
    box-shadow: 0 22px 60px rgba(16, 31, 52, .22);
}

.auth-title {
    font-size: 36px;
    font-weight: 900;
    color: #ffffff;
    margin-bottom: 4px;
}

.auth-sub {
    color: #c8d5e5;
    font-size: 15px;
    margin-bottom: 22px;
}

.hero {
    background: linear-gradient(115deg, #203653 0%, #2e557f 55%, #496f9d 100%);
    border: 1px solid #5279a5;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 22px;
    box-shadow: 0 14px 34px rgba(33, 58, 88, .16);
}

.hero h1 {
    margin: 0;
    font-size: 37px;
    font-weight: 900;
    color: #ffffff;
}

.hero p {
    margin-top: 8px;
    color: #d7e2ef;
    font-size: 16px;
}

.stat {
    background: #ffffff;
    border: 1px solid #d6dde7;
    border-radius: 18px;
    padding: 18px;
    min-height: 105px;
    box-shadow: 0 10px 26px rgba(30, 49, 77, .08);
}

.stat .value {
    font-size: 25px;
    font-weight: 900;
    color: #182230;
}

.stat .label {
    color: #6e7b8d;
    font-size: 13px;
}

.car-card {
    background: #ffffff;
    border: 1px solid #d7dfe9;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 12px 30px rgba(27, 46, 73, .08);
    min-height: 285px;
}

.car-title {
    font-size: 21px;
    font-weight: 850;
    color: #1d2a3a;
    margin-bottom: 6px;
}

.car-price {
    font-size: 24px;
    font-weight: 900;
    color: #d73a3a;
}

.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #edf4ff;
    color: #2f5f8f;
    font-size: 12px;
    font-weight: 800;
}

.meta {
    color: #556376;
    font-size: 14px;
    line-height: 1.9;
}

.seller-box {
    background: linear-gradient(145deg, #eef5fb, #f7faff);
    border: 1px solid #b8cce0;
    border-radius: 20px;
    padding: 22px;
    margin-top: 12px;
    box-shadow: 0 10px 24px rgba(47, 79, 113, .08);
}

.seller-title {
    color: #274f78;
    font-size: 20px;
    font-weight: 900;
    margin-bottom: 12px;
}

.seller-detail {
    color: #344054;
    padding: 4px 0;
}

.note {
    color: #667085;
    font-size: 12px;
}

.footer {
    text-align: center;
    color: #718096;
    padding-top: 26px;
    font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- SESSION STATE ----------------

defaults = {
    "logged_in": False,
    "guest": False,
    "user_name": "",
    "user_email": "",
    "selected_car": None,
    "auth_page": "login",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- AUTH PAGE ----------------

if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="auth-card">
            <div style="font-size:52px">🚗</div>
            <div class="auth-title">Car Prediction System</div>
            <div class="auth-sub">Find used cars that match your budget and preferences.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup, tab_guest = st.tabs(["🔐 Login", "📝 Create Account", "👤 Continue as Guest"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)
            if submit:
                if not username.strip() or not password:
                    st.warning("Please enter username and password.")
                else:
                    ok, user = authenticate(username, password)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.guest = False
                        st.session_state.user_name = user["name"]
                        st.session_state.user_email = user["email"]
                        st.session_state.selected_car = None
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with st.expander("🔑 Forgot Password"):
            with st.form("forgot_password_form"):
                reset_username = st.text_input("Username", key="reset_username")
                reset_email = st.text_input("Registered Email", key="reset_email")
                new_password = st.text_input("New Password", type="password", key="new_password")
                reset_btn = st.form_submit_button("Reset Password", use_container_width=True)
                if reset_btn:
                    ok, message = reset_password(reset_username, reset_email, new_password)
                    (st.success if ok else st.error)(message)

    with tab_signup:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name", placeholder="Rajesh Kumar")
            new_username = st.text_input("Username", placeholder="rajesh123")
            email = st.text_input("Email", placeholder="example@gmail.com")
            new_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Create Account", use_container_width=True)

            if signup_btn:
                if not full_name.strip() or not new_username.strip() or not email.strip() or not new_password:
                    st.warning("Please fill all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    ok, message = create_user(new_username, email, new_password)
                    (st.success if ok else st.error)(message)

    with tab_guest:
        st.markdown(
            "### Browse cars without creating an account\n\n"
            "Guest users can use the car search and recommendation features. "
            "For a full account experience, create an account and log in."
        )
        if st.button("👤 Continue as Guest", type="primary", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.guest = True
            st.session_state.user_name = "Guest User"
            st.session_state.user_email = ""
            st.session_state.selected_car = None
            st.rerun()

    st.markdown('<div class="footer">Buyer-focused car recommendation interface</div>', unsafe_allow_html=True)
    st.stop()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown('<div class="brand">🚗 AutoMatch</div>', unsafe_allow_html=True)
    st.caption("Buyer car search interface")
    st.divider()

    st.markdown(f"**👋 Welcome, {st.session_state.user_name}**")
    if st.session_state.guest:
        st.caption("Guest Mode")
    elif st.session_state.user_email:
        st.caption(st.session_state.user_email)

    st.markdown("### 🔎 Search Cars")

    budget = st.number_input(
        "Maximum Budget (₹)",
        min_value=10_000,
        max_value=int(df.selling_price.max()),
        value=min(1_000_000, int(df.selling_price.max())),
        step=25_000,
    )

    fuel = st.selectbox("Fuel Type", ["Any"] + sorted(df.fuel.unique()))
    transmission = st.selectbox("Transmission", ["Any"] + sorted(df.transmission.unique()))

    min_year = int(df.year.min())
    max_year = int(df.year.max())
    year = st.slider(
        "Minimum Model Year",
        min_year,
        max_year,
        max(min_year, max_year - 5),
    )

    max_km = st.number_input(
        "Maximum KM Driven",
        min_value=1_000,
        max_value=int(df.km_driven.max()),
        value=min(60_000, int(df.km_driven.max())),
        step=5_000,
    )

    owner = st.selectbox("Owner", ["Any"] + sorted(df.owner.unique()))

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.guest = False
        st.session_state.user_name = ""
        st.session_state.user_email = ""
        st.session_state.selected_car = None
        st.rerun()


# ---------------- MAIN DASHBOARD ----------------

st.markdown(
    """
    <div class="topbar">
        <div class="brand">🚗 Car Prediction System</div>
        <div class="brand-sub">Find, compare and buy used cars</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Find Your Perfect Used Car</h1>
      <p>Compare cars by budget, fuel, transmission, ownership, model year and kilometres driven.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
for col, icon, value, label in [
    (c1, "🚘", f"{len(df):,}", "Cars Available"),
    (c2, "🏭", f"{df.name.nunique():,}", "Car Models"),
    (c3, "⛽", str(df.fuel.nunique()), "Fuel Types"),
    (c4, "📅", str(max_year), "Latest Model Year"),
]:
    with col:
        st.markdown(
            f'<div class="stat"><div style="font-size:28px">{icon}</div>'
            f'<div class="value">{value}</div><div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )

# ---------------- FILTERING + SCORING ----------------

result = df[
    (df.selling_price <= budget)
    & (df.year >= year)
    & (df.km_driven <= max_km)
].copy()

if fuel != "Any":
    result = result[result.fuel == fuel]
if transmission != "Any":
    result = result[result.transmission == transmission]
if owner != "Any":
    result = result[result.owner == owner]

st.markdown("## 🎯 Recommended Cars")

if result.empty:
    st.error("No cars found. Increase your budget or relax one or more filters.")
else:
    def score(row):
        value = 0.0
        value += max(0, 35 * (1 - row.selling_price / max(budget, 1)))
        value += 20 if fuel == "Any" or row.fuel == fuel else 0
        value += 15 if transmission == "Any" or row.transmission == transmission else 0
        value += 15 if owner == "Any" or row.owner == owner else 0
        value += 15 if row.km_driven <= max_km else 0
        return min(100, max(0, value))

    result["score"] = result.apply(score, axis=1)
    result = result.sort_values(["score", "year"], ascending=False).head(6).reset_index(drop=True)

    st.success(f"Found {len(result)} top matching cars for you.")

    for start in range(0, len(result), 2):
        columns = st.columns(2, gap="large")
        for offset, column in enumerate(columns):
            index = start + offset
            if index >= len(result):
                continue

            row = result.iloc[index]
            car_key = f"{index}_{row['name']}_{int(row['year'])}"

            with column:
                st.markdown(
                    f"""
                    <div class="car-card">
                        <div class="car-title">🚘 {row['name']}</div>
                        <div class="car-price">{price(row['selling_price'])}</div>
                        <p><span class="badge">⭐ {row['score']:.0f}% Match</span></p>
                        <div class="meta">
                            📅 <b>Year:</b> {int(row['year'])}<br>
                            🛣️ <b>KM:</b> {int(row['km_driven']):,}<br>
                            ⛽ <b>Fuel:</b> {row['fuel']}<br>
                            ⚙️ <b>Transmission:</b> {row['transmission']}<br>
                            👤 <b>Owner:</b> {row['owner']}<br>
                            🏪 <b>Seller Type:</b> {row['seller_type']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("🚗 Buy This Car", key=f"buy_{car_key}", type="primary", use_container_width=True):
                    st.session_state.selected_car = {
                        "name": row["name"],
                        "price": price(row["selling_price"]),
                        "year": int(row["year"]),
                        "seller_type": row["seller_type"],
                    }
                    st.rerun()

    if st.session_state.selected_car:
        selected = st.session_state.selected_car
        st.markdown("---")
        st.markdown(
            f"""
            <div class="seller-box">
                <div class="seller-title">🤝 Seller Details</div>
                <div class="seller-detail"><b>🚘 Car:</b> {selected['name']}</div>
                <div class="seller-detail"><b>💰 Price:</b> {selected['price']}</div>
                <div class="seller-detail"><b>📅 Year:</b> {selected['year']}</div>
                <div class="seller-detail"><b>🏪 Seller Type:</b> {selected['seller_type']}</div>
                <hr style="border:0;border-top:1px solid #f0c6c6;margin:14px 0">
                <div class="seller-detail"><b>👤 Name:</b> {SELLER_DETAILS['name']}</div>
                <div class="seller-detail"><b>📞 Mobile:</b> {SELLER_DETAILS['mobile']}</div>
                <div class="seller-detail"><b>💬 WhatsApp:</b> {SELLER_DETAILS['whatsapp']}</div>
                <div class="seller-detail"><b>📧 Email:</b> {SELLER_DETAILS['email']}</div>
                <div class="seller-detail"><b>📍 Location:</b> {SELLER_DETAILS['location']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action1, action2, action3 = st.columns(3)
        with action1:
            st.link_button("📞 Call Seller", f"tel:{SELLER_DETAILS['mobile']}", use_container_width=True)
        with action2:
            st.link_button(
                "💬 WhatsApp Seller",
                f"https://wa.me/91{SELLER_DETAILS['whatsapp'][-10:]}",
                use_container_width=True,
            )
        with action3:
            st.link_button("📧 Email Seller", f"mailto:{SELLER_DETAILS['email']}", use_container_width=True)

        if st.button("✕ Close Seller Details", use_container_width=True):
            st.session_state.selected_car = None
            st.rerun()

        st.caption("Seller contact information shown here is demo data. Replace SELLER_DETAILS in app.py with your actual details.")

st.markdown(
    '<div class="footer">🚗 Car Prediction System • Buyer-focused car recommendation interface</div>',
    unsafe_allow_html=True,
)
