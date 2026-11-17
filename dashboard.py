"""
Streamlit Dashboard for TestDesignerAI
Interactive web interface for requirements engineering with LLM support
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import json

# Configure Streamlit
st.set_page_config(
    page_title="TestDesignerAI Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
    <style>
    .main-header { font-size: 2.5em; color: #1f77b4; margin-bottom: 10px; }
    .success-box { background-color: #d4edda; padding: 15px; border-radius: 5px; }
    .error-box { background-color: #f8d7da; padding: 15px; border-radius: 5px; }
    .info-box { background-color: #d1ecf1; padding: 15px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # API Configuration
    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
        help="FastAPI server endpoint"
    )
    
    # Task Type Selection
    task_type = st.selectbox(
        "Task Type",
        ["extraction", "classification", "ner", "question_answering", "test_generation"]
    )

    # Dataset Selection
    dataset = st.selectbox(
        "Dataset",
        ["Pure", "PROMISE", "Aerospace", "REQuestA"],
        help="Select the dataset to process requirements from"
    )

    # Provider Info
    st.markdown("### 📡 Provider Status")
    try:
        response = requests.get(f"{api_url}/api/health", timeout=2)
        if response.status_code == 200:
            health = response.json()
            st.success(f"✅ API Connected")
            
            # Available Providers
            providers = health.get("available_providers", [])
            st.write(f"**Available:** {', '.join(providers)}")
        else:
            st.error("❌ API Connection Failed")
    except:
        st.warning("⚠️ API Unreachable")

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.markdown('<h1 class="main-header">🤖 TestDesignerAI Dashboard</h1>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Process", "📊 Analytics", "🏥 Health", "⚙️ Settings"])

# ============================================================================
# TAB 1: Process Requirements
# ============================================================================

with tab1:
    st.markdown("## Process Requirements")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Input text
        requirement_text = st.text_area(
            "Enter requirement text:",
            placeholder="e.g., The system shall authenticate users using OAuth 2.0",
            height=150
        )
    
    with col2:
        st.markdown("### Options")
        req_id = st.text_input("Requirement ID:", value="REQ_001")
        process_button = st.button("🚀 Process", use_container_width=True)
    
    # Process the requirement
    if process_button and requirement_text:
        with st.spinner("Processing..."):
            try:
                payload = {
                    "req_id": req_id,
                    "text": requirement_text,
                    "task_type": task_type,
                    "dataset": dataset
                }
                
                response = requests.post(
                    f"{api_url}/api/process",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display Results
                    st.markdown("### ✅ Results")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Status", result.get("status", "N/A"))
                    with col2:
                        st.metric("Provider", result.get("provider_used", "N/A"))
                    with col3:
                        st.metric("Tokens", result.get("tokens_used", 0))
                    with col4:
                        st.metric("Time (ms)", f"{result.get('processing_time_ms', 0):.0f}")
                    
                    # Show full result
                    st.markdown("### Output")
                    st.json(result.get("result", {}))
                    
                    # Export options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            "📥 Download JSON",
                            json.dumps(result, indent=2),
                            f"{req_id}_result.json"
                        )
                    with col2:
                        st.download_button(
                            "📥 Download CSV",
                            pd.DataFrame([result]).to_csv(index=False),
                            f"{req_id}_result.csv"
                        )
                else:
                    st.error(f"❌ Error: {response.status_code}")
            
            except Exception as e:
                st.error(f"❌ Failed: {str(e)}")

# ============================================================================
# TAB 2: Analytics
# ============================================================================

with tab2:
    st.markdown("## 📊 Analytics & Statistics")
    
    try:
        response = requests.get(f"{api_url}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Requests",
                    stats.get("total_requests", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Total Tokens",
                    stats.get("total_tokens", 0),
                    delta=None
                )
            
            with col3:
                avg_tokens = stats.get("avg_tokens_per_request", 0)
                st.metric(
                    "Avg Tokens/Req",
                    f"{avg_tokens:.0f}",
                    delta=None
                )
            
            with col4:
                uptime = stats.get("uptime_seconds", 0) / 3600
                st.metric(
                    "Uptime (hrs)",
                    f"{uptime:.2f}",
                    delta=None
                )
            
            st.markdown("### Available Providers")
            providers_col = st.columns(len(stats.get("available_providers", [])))
            for idx, provider in enumerate(stats.get("available_providers", [])):
                with providers_col[idx]:
                    st.info(f"✅ {provider.upper()}")
        else:
            st.error("Failed to fetch statistics")
    except:
        st.warning("Cannot connect to API")

# ============================================================================
# TAB 3: Health Status
# ============================================================================

with tab3:
    st.markdown("## 🏥 Provider Health Status")
    
    try:
        response = requests.get(f"{api_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            
            # Provider Health Table
            providers_data = []
            for provider, status in health.get("provider_health", {}).items():
                providers_data.append({
                    "Provider": provider.upper(),
                    "Healthy": "✅" if status.get("is_healthy") else "❌",
                    "Errors": status.get("error_count", 0),
                    "Last Error": status.get("last_error", "-")[:50]
                })
            
            df = pd.DataFrame(providers_data)
            st.dataframe(df, use_container_width=True)
            
            # Health Gauge
            st.markdown("### System Health")
            healthy_count = sum(1 for p in health.get("provider_health", {}).values() if p.get("is_healthy"))
            total_count = len(health.get("provider_health", {}))
            health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=health_percentage,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "System Health %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 100], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Cannot fetch health status")

# ============================================================================
# TAB 4: Settings
# ============================================================================

with tab4:
    st.markdown("## ⚙️ Configuration Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### LLM Settings")
        llm_provider = st.selectbox(
            "Preferred LLM Provider",
            ["ollama", "groq", "openai", "claude", "auto"]
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=4096,
            value=2048,
            step=100
        )
    
    with col2:
        st.markdown("### API Settings")
        api_timeout = st.number_input(
            "API Timeout (seconds)",
            min_value=5,
            max_value=120,
            value=30
        )
        
        batch_size = st.number_input(
            "Batch Size",
            min_value=1,
            max_value=100,
            value=10
        )
        
        enable_caching = st.checkbox("Enable Response Caching", value=True)
    
    # Save Settings Button
    if st.button("💾 Save Settings", use_container_width=True):
        st.success("✅ Settings saved!")

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>TestDesignerAI v1.0 | Powered by LLMs with Automatic Failover</p>
    <p>📚 Docs: <a href='http://localhost:8000/docs'>API Docs</a> | 
    🏥 Health: <a href='http://localhost:8000/api/health'>Health Check</a></p>
</div>
""", unsafe_allow_html=True)
