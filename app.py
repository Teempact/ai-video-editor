# Add this to the top of your existing app.py

import streamlit as st
import os
from datetime import datetime, timedelta

# Public version enhancements
st.set_page_config(
    page_title="🎬 AI Video Editor - Public Version",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Usage tracking (optional)
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()
    st.session_state.videos_created = 0

# Add at the top of your app, after the main header
st.markdown("""
<div style='background: linear-gradient(90deg, #FF6B6B, #4ECDC4); color: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center;'>
    <h3>🌍 Public AI Video Editor</h3>
    <p>Create professional videos in minutes • Free to use • No signup required</p>
</div>
""", unsafe_allow_html=True)

# Usage stats in sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 Session Stats")
    
    session_duration = datetime.now() - st.session_state.session_start
    st.metric("⏱️ Session Time", f"{session_duration.seconds // 60} min")
    st.metric("🎬 Videos Created", st.session_state.videos_created)
    
    # Tips for public users
    st.subheader("💡 Public User Tips")
    st.info("""
    • Files are temporary and auto-deleted
    • Download your content immediately
    • Share this URL with others!
    • No login required
    """)
    
    # Creator info
    st.subheader("👨‍💻 About This App")
    st.success("""
    **Created by:** [Your Name]
    **Purpose:** Free AI video creation
    **Tech:** Streamlit + Python
    **Source:** Available on request
    """)

# Add at the end of successful video generation
def increment_video_counter():
    st.session_state.videos_created += 1

# Add this function call after successful video generation:
# increment_video_counter()

# Footer for public version
st.markdown("""
---
<div style='text-align: center; color: #666; padding: 2rem;'>
    <h4>🚀 Enjoying this free AI video editor?</h4>
    <p><strong>Share the URL:</strong> Help others create amazing videos too!</p>
    <p><strong>Need help?</strong> This app creates audio + images. Use any video editor to combine them.</p>
    <p><em>Made with ❤️ using Python and Streamlit • No data stored • Privacy-friendly</em></p>
</div>
""", unsafe_allow_html=True)
