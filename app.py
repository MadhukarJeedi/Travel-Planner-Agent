import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/travel"
REQUEST_TIMEOUT = 90  # seconds

# Page Configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Session State Initialization
if "history" not in st.session_state:
    st.session_state.history = []

if "selected_place" not in st.session_state:
    st.session_state.selected_place = None

if "current_view" not in st.session_state:
    st.session_state.current_view = None

# Custom CSS
st.markdown("""
<style>
.main {
    padding-top: 1rem;
}
.hero {
    background: linear-gradient(90deg, #1f4e79, #4f8bf9);
    padding: 30px;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}
/* Styles the native streamlit container to act as a sleek card border */
div[data-testid="stContainer"] {
    background-color: #f8f9fa;
    padding: 10px 20px;
    border-radius: 15px;
    border-left: 6px solid #4f8bf9;
}
.stButton > button {
    width: 100%;
    height: 3rem;
    border-radius: 10px;
    font-size: 16px;
    font-weight: bold;
}
.feature-box {
    background-color: #f1f3f6;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero">
    <h1>✈️ AI Travel Planner Agent</h1>
    <h4>Plan smarter trips with AI-powered itineraries</h4>
    <p>Weather • Tourist Attractions • Railway Information • Routes • Travel Tips</p>
</div>
""", unsafe_allow_html=True)

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(" Destinations", "500+")
with col2:
    st.metric(" Weather", "Live")
with col3:
    st.metric(" Railways", "Available")
with col4:
    st.metric(" AI Model", "Groq")

st.divider()

# Features Section
st.subheader(" What Can I Do?")
f1, f2, f3, f4 = st.columns(4)
with f1:
    st.markdown('<div class="feature-box">🌤️<br><b>Weather Forecast</b></div>', unsafe_allow_html=True)
with f2:
    st.markdown('<div class="feature-box">📍<br><b>Tourist Attractions</b></div>', unsafe_allow_html=True)
with f3:
    st.markdown('<div class="feature-box">🚆<br><b>Train Information</b></div>', unsafe_allow_html=True)
with f4:
    st.markdown('<div class="feature-box">🗺️<br><b>Route Planning</b></div>', unsafe_allow_html=True)

st.divider()

# Input Section
st.subheader("🧳 Plan Your Journey")
query = st.text_area(
    "Ask your travel question",
    placeholder="Example: Plan a 3-day trip to Goa from Hyderabad"
)

# Generate Button
if st.button("🚀 Generate Travel Plan"):
    if not query.strip():
        st.warning("Please enter a travel-related question.")
    else:
        with st.spinner("✈️ Creating your travel plan..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"query": query},
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.Timeout:
                st.error("The request timed out. The travel agent may be taking too long — try again.")
                result = None
            except requests.exceptions.ConnectionError:
                st.error("Couldn't reach the travel planner API. Make sure the FastAPI backend is running.")
                result = None
            except requests.exceptions.HTTPError as e:
                st.error(f"API returned an error: {e}")
                result = None
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                result = None

            if result is not None:
                if result.get("status") != "success":
                    st.error(result.get("message", "The travel planner couldn't process your request."))
                else:
                    new_plan = {
                        "query": query,
                        "response": result["response"],
                        "images": result.get("images", [])
                    }
                    st.session_state.history.append(new_plan)
                    st.session_state.current_view = new_plan
                    st.success("Travel Plan Generated Successfully!")

# Display current active plan
if st.session_state.current_view:
    active = st.session_state.current_view

    st.subheader("📋 Your Personalized Travel Plan")
    
    # Native markdown container ensures italics, bolding, and lists render accurately
    with st.container(border=True):
        st.markdown(active["response"])

    if active.get("images"):
        st.subheader("📸 Tourist Attractions")
        st.caption("💡 Click 'Explore Gallery' inside any card below to view its full collection of images.")
        
        cols = st.columns(3)
        for idx, item in enumerate(active["images"]):
            with cols[idx % 3]:
                with st.container(border=True):
                    if item.get("cover_image"):
                        st.image(item["cover_image"], use_container_width=True)
                    else:
                        st.caption("No image available")

                    st.markdown(f"#### 📍 {item['name']}")
                    
                    if item.get("gallery"):
                        if st.button(f"✨ Explore {item['name']}", key=f"img_click_{idx}"):
                            st.session_state.selected_place = item
                            st.rerun()

# Gallery View (Triggers dynamically below your itinerary when an image card's explore button is tapped)
if st.session_state.selected_place:
    place = st.session_state.selected_place
    st.divider()

    header_col, close_col = st.columns([6, 1])
    with header_col:
        st.subheader(f"📸 {place['name']} Gallery Collection")
    with close_col:
        if st.button("✖ Close Gallery"):
            st.session_state.selected_place = None
            st.rerun()

    if st.session_state.selected_place:
        gallery_cols = st.columns(3)
        for idx, image in enumerate(place.get("gallery", [])):
            with gallery_cols[idx % 3]:
                st.image(image, use_container_width=True)

# Sidebar
with st.sidebar:
    st.title("✈️ Travel Assistant")
    st.info("AI-powered travel planner using FastAPI, LangGraph, Groq, Geoapify, and travel tools.")
    st.divider()

    st.subheader("🕘 Query History")
    if not st.session_state.history:
        st.caption("No queries asked yet")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            title = item["query"][:40] + "..." if len(item["query"]) > 40 else item["query"]
            if st.button(title, key=f"history_{idx}"):
                st.session_state.current_view = item
                st.rerun()

    st.divider()
    st.subheader("💡 Sample Questions")
    st.markdown("""
    - Plan a 3-day trip to Goa
    - Best tourist places in Jaipur
    - Weather in Manali this week
    """)

st.divider()
st.caption("THIS ABOVE INFORMATION IS TAKEN FROM LIVE API DATA")