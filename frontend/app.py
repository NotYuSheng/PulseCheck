import streamlit as st
import requests
import yaml
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Pulse Check UI", layout="centered")
st.title("🧩 Pulse Check – Service Registry")

tab1, tab2 = st.tabs(["📋 Register Service", "📡 Service Dashboard"])

with tab1:
    st.subheader("Register a Service")

    with st.expander("📘 How to onboard a service"):
        st.markdown("""
        To be monitored by Pulse Check, your service **must expose a `/health`-like endpoint** that returns **HTTP 200 OK**.

        You can register services using either:
        - IP and port: `192.168.1.10:8080/health`
        - Local DNS or domain: `my-service.local/health`
        - HTTPS endpoints: `https://example.com/status`

        Here's a minimal example in **FastAPI**:
        """)

        st.code("""# example_service/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)
""", language="python")

        st.markdown("""
        Run it with:

        ```bash
        uvicorn main:app --host 0.0.0.0 --port 8080
        ```

        Then register: `192.168.1.10:8080/health`
        """)

    with st.form("register_form"):
        name = st.text_input("Service Name", placeholder="e.g. My API Service")
        description = st.text_input("Description", placeholder="e.g. Handles user authentication")
        healthcheck_url = st.text_input(
            "Health Check URL (IP/domain + optional path)",
            placeholder="e.g. 192.168.1.10:8080/health or my-service.local/status"
        )

        submitted = st.form_submit_button("Register")

        if submitted:
            if not healthcheck_url:
                st.error("Please provide a valid IP address, domain, and optional path.")
            else:
                # Build the full URL safely
                full_url = healthcheck_url.strip()
                if full_url and not full_url.startswith("http://") and not full_url.startswith("https://"):
                    full_url = "http://" + full_url

                # Show preview of what will be registered
                if full_url:
                    st.markdown(f"📡 Will register health check at: `{full_url}`")

                payload = {
                    "name": name,
                    "description": description,
                    "healthcheck_url": full_url
                }

                try:
                    resp = requests.post(f"{BACKEND_URL}/register", json=payload)

                    if resp.status_code == 200:
                        st.success("✅ Service registered successfully!")
                        st.json(payload)
                    else:
                        st.error(f"❌ Failed to register: {resp.text}")
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")

with tab2:
    st.subheader("📡 Registered Services")

    # Get value from session_state (set by the dropdown below)
    refresh_interval = st.session_state.get("refresh_interval", 10)

    with st.container(height=None, border=None, key=None):
        # Visually hide the autorefresh iframe
        st.markdown("<style>.element-container:has(iframe[title='streamlit_autorefresh.st_autorefresh']) { display: none; }</style>", unsafe_allow_html=True)
        refresh_count = st_autorefresh(
            interval=refresh_interval * 1000,
            key="dashboard_refresh"
        ) if refresh_interval > 0 else 0

    # Track previous statuses
    if "last_statuses" not in st.session_state:
        st.session_state.last_statuses = {}

    try:
        if refresh_count > 0:
            try:
                requests.get(f"{BACKEND_URL}/ping")
            except Exception as e:
                st.warning("⚠️ Auto-ping failed.")

        services = requests.get(f"{BACKEND_URL}/services").json()

        if not services:
            st.info("No services registered yet.")
        else:
            column_size = [2, 3, 4, 2.5, 2.5]
            cols = st.columns(column_size)
            cols[0].markdown("**🛠 Name**")
            cols[1].markdown("**📝 Description**")
            cols[2].markdown("**🔗 Healthcheck URL**")
            cols[3].markdown("**📶 Status**")
            cols[4].markdown("**❌ Remove**")

            for name, info in services.items():
                status = info.get("status", "unknown")
                prev_status = st.session_state.last_statuses.get(name)

                # 🔔 Degraded status toast
                if prev_status != status and status in ["unhealthy", "unreachable"]:
                    st.toast(f"⚠️ '{name}' is now {status.upper()}!", icon="🚨")

                # ✅ Recovery toast
                elif prev_status != status and status == "healthy" and prev_status in ["unhealthy", "unreachable"]:
                    st.toast(f"✅ '{name}' has recovered and is now HEALTHY.", icon="🎉")

                # Update last known status
                st.session_state.last_statuses[name] = status

                # Define emoji mapping for statuses
                emoji_map = {
                    "healthy": "🟢",
                    "unhealthy": "🟠",
                    "unreachable": "🔴",
                    "not checked": "⚪",
                    "unknown": "⚪"
                }
                status_emoji = emoji_map.get(status, "⚪")

                # Render each service row
                row = st.columns(column_size)
                row[0].markdown(f"**{name}**")
                row[1].markdown(info["description"])
                row[2].code(info["healthcheck_url"], language="bash")
                row[3].markdown(f"{status_emoji} **{status.capitalize()}**")

                if row[4].button("🗑️", key=f"remove_{name}"):
                    try:
                        resp = requests.delete(f"{BACKEND_URL}/services/{name}")
                        if resp.status_code == 200:
                            st.success(f"Removed '{name}'")
                            st.rerun()
                        else:
                            st.error(f"Failed to remove: {resp.text}")
                    except Exception as e:
                        st.error(f"Error removing service: {e}")

        st.divider()
        # Two-column layout: dropdown on left, refresh button on right
        col_left, col_right = st.columns([8, 2])

        with col_left:
            st.selectbox(
                "Auto-refresh interval",
                options=[0, 5, 10, 30, 60],
                format_func=lambda x: f"{x} seconds" if x > 0 else "Manual only",
                index=2,
                key="refresh_interval"
            )

        with col_right:
            st.markdown("<div style='padding-top: 1.8em'></div>", unsafe_allow_html=True)
            if st.button("🔄 Refresh"):
                try:
                    resp = requests.get(f"{BACKEND_URL}/ping").json()
                    st.success(resp["message"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to ping services: {e}")

        # Display last refresh time
        last_refresh = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        st.markdown(f"🕒 Last refresh: `{last_refresh}`")

    except Exception as e:
        st.error(f"Could not load services: {e}")
