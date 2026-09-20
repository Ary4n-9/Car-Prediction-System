import streamlit as st
import pandas as pd
from urllib.parse import quote
st.set_page_config(page_title="Car Prediction System", page_icon="🚗", layout="wide")

DATA_FILE = "car_details.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    required = ["name","year","selling_price","km_driven","fuel","seller_type","transmission","owner"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("Missing columns: " + ", ".join(missing))
        st.stop()
    for c in ["year","selling_price","km_driven"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["name","fuel","seller_type","transmission","owner"]:
        df[c] = df[c].astype(str).str.strip()
    return df.dropna(subset=required).reset_index(drop=True)

df = load_data()

def image_url(name, i=0):
    q = quote(str(name) + " car")
    return f"https://loremflickr.com/900/520/{q}?lock={(abs(hash(str(name)))+i)%1000}"

def price(v):
    return f"₹{int(v):,}"

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 0%,#132a4b,transparent 30%),#07101f;color:#f8fafc}
[data-testid="stSidebar"]{background:#09111f;border-right:1px solid #24446f}
.hero,.metric,.car,.prediction{background:linear-gradient(145deg,#10254a,#0b1629);
border:1px solid #294a75;border-radius:20px;box-shadow:0 15px 45px #0004}
.hero{padding:35px;margin-bottom:25px}.hero h1{font-size:38px;color:white;margin:0}
.hero p{color:#aebed3;font-size:16px}.metric{padding:20px;text-align:center;min-height:120px}
.metric .v{font-size:27px;font-weight:800;color:white}.metric .l{color:#8fa5c1}
.car{padding:20px;margin-bottom:20px}.car h2{font-size:21px;color:white}
.car .price{font-size:25px;font-weight:800;color:#60a5fa}
.match{display:inline-block;background:#123d35;color:#62e6b7;padding:6px 10px;border-radius:20px}
.prediction{padding:28px;margin-top:25px}.bigprice{font-size:35px;font-weight:900;color:#67e8f9}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
    <div style="max-width:650px;margin:70px auto;text-align:center">
      <div class="hero">
        <div style="font-size:55px">🚗</div>
        <h1>Car Prediction System</h1>
        <p>Smart used-car recommendation & price prediction</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login"):
        name = st.text_input("Full Name", placeholder="Enter your name")
        email = st.text_input("Email Address", placeholder="example@gmail.com")
        contact = st.text_input("Contact Number", placeholder="Enter mobile number")
        if st.form_submit_button("🚀 Enter Car Prediction System", use_container_width=True):
            if name.strip() and email.strip() and contact.strip():
                st.session_state.logged_in = True
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.warning("Please fill all fields.")
    st.stop()

with st.sidebar:
    st.markdown("## 🚗 Car Prediction System")
    st.write("👋 Welcome,", st.session_state.get("user_name","User"))
    st.divider()
    st.markdown("### 🔎 Search Filters")
    budget = st.number_input("💰 Maximum Budget (₹)", 10000, int(df.selling_price.max()),
                             min(1000000, int(df.selling_price.max())), 25000)
    fuel = st.selectbox("⛽ Fuel Type", ["Any"] + sorted(df.fuel.unique()))
    transmission = st.selectbox("⚙️ Transmission", ["Any"] + sorted(df.transmission.unique()))
    min_year = int(df.year.min()); max_year = int(df.year.max())
    year = st.slider("📅 Minimum Year", min_year, max_year, max(min_year,max_year-5))
    max_km = st.number_input("🛣️ Maximum KM Driven", 1000, int(df.km_driven.max()),
                             min(60000,int(df.km_driven.max())), 5000)
    owner = st.selectbox("👤 Owner", ["Any"] + sorted(df.owner.unique()))
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in=False
        st.rerun()

st.markdown("""
<div class="hero">
<h1>🚗 Find Your Perfect Used Car</h1>
<p>Search used cars using your budget, fuel, transmission, ownership and driving requirements.</p>
</div>
""", unsafe_allow_html=True)

a,b,c,d=st.columns(4)
for col,icon,value,label in [
    (a,"🚘",f"{len(df):,}","Cars Available"),
    (b,"🏭",f"{df.name.nunique():,}","Car Models"),
    (c,"⛽",str(df.fuel.nunique()),"Fuel Types"),
    (d,"📅",str(max_year),"Latest Model Year")]:
    with col:
        st.markdown(f'<div class="metric"><div style="font-size:30px">{icon}</div><div class="v">{value}</div><div class="l">{label}</div></div>',unsafe_allow_html=True)

r=df[(df.selling_price<=budget)&(df.year>=year)&(df.km_driven<=max_km)].copy()
if fuel!="Any": r=r[r.fuel==fuel]
if transmission!="Any": r=r[r.transmission==transmission]
if owner!="Any": r=r[r.owner==owner]

st.markdown("## 🎯 Recommended Cars")
if r.empty:
    st.error("No cars found. Increase budget or relax filters.")
else:
    # A transparent match score based on how well each car fits selected filters.
    def score(row):
        s=0
        s += max(0, 35*(1-row.selling_price/max(budget,1)))
        s += 20 if fuel=="Any" or row.fuel==fuel else 0
        s += 15 if transmission=="Any" or row.transmission==transmission else 0
        s += 15 if owner=="Any" or row.owner==owner else 0
        s += 15 if row.km_driven<=max_km else 0
        return min(100,max(0,s))
    r["score"]=r.apply(score,axis=1).sort_values if False else r.apply(score,axis=1)
    r=r.sort_values(["score","year"],ascending=False).head(6).reset_index(drop=True)
    st.success(f"Found {len(r)} top matching cars.")
    for start in range(0,len(r),2):
        cols=st.columns(2)
        for j,col in enumerate(cols):
            i=start+j
            if i>=len(r): continue
            row=r.iloc[i]
            with col:
                st.image(image_url(row["name"],i),use_container_width=True,caption=row["name"])
                st.markdown(f"""
                <div class="car">
                <h2>🚘 {row["name"]}</h2>
                <div class="price">{price(row["selling_price"])}</div>
                <span class="match">⭐ {row["score"]:.0f}% Match</span>
                <p>📅 <b>Year:</b> {int(row["year"])} &nbsp; 🛣️ <b>KM:</b> {int(row["km_driven"]):,}</p>
                <p>⛽ <b>Fuel:</b> {row["fuel"]} &nbsp; ⚙️ <b>Transmission:</b> {row["transmission"]}</p>
                <p>👤 <b>Owner:</b> {row["owner"]} &nbsp; 🏪 <b>Seller:</b> {row["seller_type"]}</p>
                </div>
                """,unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#71839d;padding:15px">🚗 Car Prediction System • Streamlit</div>',unsafe_allow_html=True)
