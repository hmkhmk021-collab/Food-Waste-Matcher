import streamlit as st
from db import (
    init_db, get_restaurants, post_surplus, find_best_matches,
    confirm_pickup, get_impact_stats
)

st.set_page_config(page_title="Food Waste Matcher AI", page_icon="🌾", layout="wide")
init_db()

# ---------- Custom Styling: Dashboard Dark Theme ----------
st.markdown("""
<style>
    .welcome-banner {
        background: linear-gradient(135deg, #FF4B4B22, #1C2029);
        border: 1px solid #2A2F3A;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
    }
    .welcome-title {
        font-size: 24px;
        font-weight: 800;
        color: #FAFAFA;
        margin: 0;
    }
    .welcome-sub {
        font-size: 13px;
        color: #9AA0AC;
        margin: 4px 0 0 0;
    }
    .stat-card {
        background: #1C2029;
        border: 1px solid #2A2F3A;
        border-radius: 14px;
        padding: 18px 16px;
    }
    .stat-icon {
        width: 34px;
        height: 34px;
        border-radius: 9px;
        background: #2A2F3A;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
        margin-bottom: 10px;
    }
    .stat-number {
        font-size: 26px;
        font-weight: 800;
        color: #FAFAFA;
    }
    .stat-label {
        font-size: 12px;
        color: #9AA0AC;
    }
    .section-card {
        background: #1C2029;
        border: 1px solid #2A2F3A;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 18px;
    }
    .section-title {
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 4px;
        color: #FAFAFA;
    }
    .match-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
        background: #262B36;
    }
    .match-row.top {
        background: #3A2020;
        border: 1.5px solid #FF4B4B;
    }
    .rank-circle {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 800;
        color: white;
        flex-shrink: 0;
    }
    .rank-1 { background: #FF4B4B; }
    .rank-other { background: #4A4F5A; }
    .best-badge {
        background: #FF4B4B;
        color: white;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🌾 Food Waste Matcher")
    st.markdown("---")
    st.markdown("📊 **Dashboard**")
    st.markdown("🏪 Post Surplus")
    st.markdown("🤝 NGO Matches")
    st.markdown("📈 Impact Reports")
    st.markdown("---")
    st.caption("AI-powered surplus food matching for Pakistan")

# ---------- Welcome Banner ----------
st.markdown("""
<div class="welcome-banner">
    <p class="welcome-title">👋 Welcome back!</p>
    <p class="welcome-sub">Here's what's happening with surplus food matching today</p>
</div>
""", unsafe_allow_html=True)

# ---------- Session State ----------
if "last_post_id" not in st.session_state:
    st.session_state.last_post_id = None
if "matches" not in st.session_state:
    st.session_state.matches = []
if "restaurant" not in st.session_state:
    st.session_state.restaurant = None
if "item_name" not in st.session_state:
    st.session_state.item_name = ""
if "quantity" not in st.session_state:
    st.session_state.quantity = 0

# ---------- Impact Stats + Chart Row ----------
stats = get_impact_stats()
col_stats, col_chart = st.columns([1, 1.3])

with col_stats:
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">🚚</div>
            <div class="stat-number">{stats["pickups"]}</div>
            <div class="stat-label">Pickups done</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">🍲</div>
            <div class="stat-number">{stats["meals_saved"]}</div>
            <div class="stat-label">Meals saved</div>
        </div>""", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-number">{stats["people_helped"]}</div>
        <div class="stat-label">People helped this week</div>
    </div>""", unsafe_allow_html=True)

with col_chart:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">📈 Weekly impact trend</p>', unsafe_allow_html=True)
    chart_data = {
        "Mon": 8, "Tue": 12, "Wed": 15, "Thu": 10, "Fri": 22, "Sat": 30, "Sun": stats["meals_saved"] + 5
    }
    st.bar_chart(chart_data, color="#FF4B4B")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# ---------- Restaurant Side: Post Surplus ----------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<p class="section-title">🏪 Post surplus food</p>', unsafe_allow_html=True)

restaurants = get_restaurants()
restaurant_names = {r["name"]: r for r in restaurants}

col1, col2 = st.columns(2)
with col1:
    selected_name = st.selectbox("Restaurant", list(restaurant_names.keys()))
    item_name = st.text_input("Item name", placeholder="e.g. Bread, Rice, Curry")
with col2:
    quantity = st.number_input("Quantity", min_value=1, value=10)
    expiry_minutes = st.number_input("Expires in (minutes)", min_value=1, value=30)

if st.button("🚀 Post and find matches", type="primary", use_container_width=True):
    if not item_name.strip():
        st.warning("Please enter an item name.")
    else:
        restaurant = restaurant_names[selected_name]
        post_id = post_surplus(restaurant["id"], item_name, quantity, expiry_minutes)
        matches = find_best_matches(restaurant["latitude"], restaurant["longitude"], expiry_minutes, quantity)

        st.session_state.last_post_id = post_id
        st.session_state.matches = matches
        st.session_state.restaurant = restaurant
        st.session_state.item_name = item_name
        st.session_state.quantity = quantity

        st.success(f"Posted: {quantity}x {item_name} from {restaurant['name']}")

st.markdown('</div>', unsafe_allow_html=True)

# ---------- NGO Side: AI Matches ----------
if st.session_state.matches:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">🤝 AI-suggested matches</p>', unsafe_allow_html=True)
    st.caption(f"Ranked by distance and urgency for {st.session_state.quantity}x {st.session_state.item_name}")

    for i, m in enumerate(st.session_state.matches, 1):
        row_class = "match-row top" if i == 1 else "match-row"
        rank_class = "rank-circle rank-1" if i == 1 else "rank-circle rank-other"
        badge = '<span class="best-badge">Best match</span>' if i == 1 else f'<span style="font-size:12px; color:#9AA0AC;">Score {m["score"]}</span>'
        st.markdown(f"""
        <div class="{row_class}">
            <div class="{rank_class}">{i}</div>
            <div style="flex:1;">
                <div style="font-weight:700; font-size:14px; color:#FAFAFA;">{m['ngo_name']}</div>
                <div style="font-size:12px; color:#9AA0AC;">{m['distance_km']} km away</div>
            </div>
            {badge}
        </div>
        """, unsafe_allow_html=True)

    top_match = st.session_state.matches[0]
    if st.button(f"✅ Confirm pickup — {top_match['ngo_name']}", use_container_width=True):
        confirm_pickup(st.session_state.last_post_id, top_match["ngo_name"])
        st.balloons()
        st.success(f"Pickup confirmed! {top_match['ngo_name']} will collect the food.")
        st.session_state.matches = []
        st.session_state.last_post_id = None
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No active surplus posts. Post surplus food above to see AI matching in action.")
