import streamlit as st
from db import (
    init_db, get_restaurants, post_surplus, find_best_matches,
    confirm_pickup, get_impact_stats
)

st.set_page_config(page_title="Food Waste Matcher AI", page_icon="🌿", layout="centered")
init_db()

# ---------- Custom Styling: Modern Infographic Theme ----------
st.markdown("""
<style>
    .header-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 10px 0 20px 0;
    }
    .header-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: #1D9E75;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        flex-shrink: 0;
    }
    .header-title {
        font-size: 22px;
        font-weight: 700;
        color: #0F1F19;
        margin: 0;
    }
    .header-sub {
        font-size: 13px;
        color: #6B7A73;
        margin: 0;
    }
    .stat-card {
        background: #F5F7F5;
        border-radius: 14px;
        padding: 18px 14px;
        text-align: left;
    }
    .stat-icon {
        width: 34px;
        height: 34px;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
        margin-bottom: 10px;
    }
    .stat-number {
        font-size: 24px;
        font-weight: 700;
        color: #0F1F19;
    }
    .stat-label {
        font-size: 12px;
        color: #6B7A73;
    }
    .section-card {
        background: #FFFFFF;
        border: 1px solid #E7EBE8;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .section-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #0F1F19;
    }
    .match-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
    }
    .match-row.top {
        background: #EAF6EF;
        border: 1px solid #1D9E75;
    }
    .rank-circle {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        color: white;
        flex-shrink: 0;
    }
    .rank-1 { background: #1D9E75; }
    .rank-other { background: #B4B2A9; }
    .best-badge {
        background: #1D9E75;
        color: white;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-row">
    <div class="header-icon">🌿</div>
    <div>
        <p class="header-title">Food Waste Matcher</p>
        <p class="header-sub">Surplus food, matched in real time</p>
    </div>
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

# ---------- Impact Dashboard ----------
stats = get_impact_stats()
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-icon" style="background:#DDF0E6;">🚚</div>
        <div class="stat-number">{stats["pickups"]}</div>
        <div class="stat-label">Pickups done</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-icon" style="background:#DFF0F5;">🍲</div>
        <div class="stat-number">{stats["meals_saved"]}</div>
        <div class="stat-label">Meals saved</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-icon" style="background:#FBEAD9;">👥</div>
        <div class="stat-number">{stats["people_helped"]}</div>
        <div class="stat-label">People helped</div>
    </div>""", unsafe_allow_html=True)

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
        badge = '<span class="best-badge">Best match</span>' if i == 1 else f'<span style="font-size:12px; color:#9AA39D;">Score {m["score"]}</span>'
        st.markdown(f"""
        <div class="{row_class}">
            <div class="{rank_class}">{i}</div>
            <div style="flex:1;">
                <div style="font-weight:600; font-size:14px; color:#0F1F19;">{m['ngo_name']}</div>
                <div style="font-size:12px; color:#6B7A73;">{m['distance_km']} km away</div>
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
