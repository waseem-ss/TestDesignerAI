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
import os

# Configure Streamlit
st.set_page_config(
    page_title="TestDesignerAI Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# Cached GET helper, defined before the tabs because the LLM Settings tab uses it.
@st.cache_data(ttl=30, show_spinner=False)
def fetch_json(url: str):
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()


# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.markdown('<h1 class="main-header">🤖 TestDesignerAI Dashboard</h1>', unsafe_allow_html=True)

# API URL (default from the TESTDESIGNER_API_URL environment variable, else localhost:8000)
api_url = st.text_input(
    "API URL",
    value=os.getenv("TESTDESIGNER_API_URL", "http://localhost:8000"),
    help="FastAPI server endpoint",
).rstrip("/")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📝 Process Requirements", "📊 Analytics", "🏥 Health", "⚙️ LLM Settings", "🧪 Test Case Designer"]
)

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
        task_type = st.selectbox(
            "Task Type",
            ["extraction", "classification", "ner", "question_answering", "test_generation"]
        )
        dataset = st.selectbox(
            "Dataset",
            ["Pure", "PROMISE", "Aerospace", "REQuestA"],
            help="Dataset the requirement is processed against"
        )
        process_provider = st.selectbox(
            "LLM Provider",
            ["ollama", "hf", "gemini", "groq"],
            key="process_provider",
        )
        try:
            process_models_info = fetch_json(f"{api_url}/api/models?provider={process_provider}")
            process_models = process_models_info["models"]
            process_default = process_models_info.get("default")
        except Exception as e:
            st.caption(f"⚠️ Cannot load models for {process_provider}: {e}")
            process_models, process_default = [], None
        if process_models:
            process_model = st.selectbox(
                "Model", process_models,
                index=(process_models.index(process_default) if process_default in process_models else 0),
                key="process_model",
            )
        else:
            process_model = None
            st.caption(f"No models for {process_provider}. Ollama: start Ollama. Cloud: set the API key in .env.")
        process_button = st.button("🚀 Process", use_container_width=True)
    
    # Process the requirement
    if process_button and requirement_text:
        with st.spinner("Processing..."):
            try:
                payload = {
                    "req_id": req_id,
                    "text": requirement_text,
                    "task_type": task_type,
                    "dataset": dataset,
                    "provider": process_provider,
                    "llm_model": process_model,
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
        response = requests.get(f"{api_url}/api/analytics", timeout=30)
        response.raise_for_status()
        analytics = response.json()
    except Exception as e:
        analytics = None
        st.warning(f"Cannot load analytics from the API: {e}")

    if analytics:
        totals = analytics["totals"]
        live = analytics.get("live", {})

        st.markdown("### Generation totals (all saved runs)")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Runs", totals["runs"])
        k2.metric("Rows generated", totals["rows_generated"])
        k3.metric("Test cases", totals["test_cases"])
        k4.metric("Avg cases / row", f"{totals['avg_cases_per_row']:.2f}")
        k5.metric("Datasets", totals["datasets"])

        st.markdown("### Live API counters (since the API started)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Process requests", live.get("total_requests", 0))
        c2.metric("Tokens used", live.get("total_tokens", 0))
        avg_tokens = live.get("total_tokens", 0) / max(1, live.get("total_requests", 0))
        c3.metric("Avg tokens / request", f"{avg_tokens:.0f}")
        c4.metric("Uptime (hrs)", f"{live.get('uptime_seconds', 0) / 3600:.2f}")

        runs = pd.DataFrame(analytics["runs"])
        if runs.empty:
            st.info("No test-generation runs yet. Generate test cases in the Test Case Designer tab.")
        else:
            all_providers = sorted(runs["provider"].unique())
            chosen = st.multiselect("Providers", all_providers, default=all_providers, key="analytics_providers")
            runs = runs[runs["provider"].isin(chosen)]

            if runs.empty:
                st.info("No runs for the selected providers.")
            else:
                st.markdown("### Test cases by provider and model")
                by_model = (runs.groupby(["provider", "model"], as_index=False)
                            .agg(test_cases=("test_cases", "sum"), rows=("rows_saved", "sum")))
                by_model["label"] = by_model["provider"] + " · " + by_model["model"]
                fig = go.Figure(go.Bar(
                    x=by_model["label"], y=by_model["test_cases"],
                    text=by_model["test_cases"], textposition="auto",
                    customdata=by_model["rows"],
                    hovertemplate="%{x}<br>Test cases: %{y}<br>Rows: %{customdata}<extra></extra>",
                ))
                fig.update_layout(height=340, margin=dict(t=20, b=20), yaxis_title="Test cases")
                st.plotly_chart(fig, use_container_width=True)

                left, right = st.columns(2)
                with left:
                    st.markdown("### Avg test cases per row by template")
                    by_tpl = (runs.groupby("template", as_index=False)
                              .agg(test_cases=("test_cases", "sum"), rows=("rows_saved", "sum")))
                    by_tpl["avg"] = by_tpl["test_cases"] / by_tpl["rows"].where(by_tpl["rows"] > 0)
                    fig = go.Figure(go.Bar(x=by_tpl["template"], y=by_tpl["avg"].fillna(0),
                                           text=by_tpl["avg"].round(2), textposition="auto"))
                    fig.update_layout(height=300, margin=dict(t=20, b=20), yaxis_title="Avg cases / row")
                    st.plotly_chart(fig, use_container_width=True)

                with right:
                    st.markdown("### Test cases per run over time")
                    timeline = runs.copy()
                    timeline["started"] = pd.to_datetime(timeline["started_at"], errors="coerce")
                    timeline = timeline.dropna(subset=["started"]).sort_values("started")
                    fig = go.Figure()
                    for prov, grp in timeline.groupby("provider"):
                        fig.add_trace(go.Scatter(
                            x=grp["started"], y=grp["test_cases"], mode="markers", name=prov,
                            text=grp["dataset"] + " · " + grp["rows_saved"].astype(str) + " rows",
                            hovertemplate="%{x}<br>%{y} test cases<br>%{text}<extra>" + prov + "</extra>",
                        ))
                    fig.update_layout(height=300, margin=dict(t=20, b=20), yaxis_title="Test cases")
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Success rate per run")
                runs_view = runs.copy()
                runs_view["success_%"] = (100 * runs_view["rows_saved"] / runs_view["rows_planned"].where(
                    runs_view["rows_planned"] > 0)).fillna(0).round(0).astype(int)
                st.dataframe(
                    runs_view[["started_at", "template", "dataset", "provider", "model",
                               "rows_planned", "rows_saved", "success_%", "test_cases",
                               "avg_cases_per_row", "run"]],
                    use_container_width=True, hide_index=True,
                )

        if analytics.get("skipped"):
            with st.expander(f"{len(analytics['skipped'])} folder(s) could not be read"):
                for item in analytics["skipped"]:
                    st.text(item)

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
                    "Last Error": (status.get("last_error") or "-")[:50]
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
    except Exception as e:
        st.warning(f"Cannot fetch health status: {e}")

# ============================================================================
# TAB 4: Settings
# ============================================================================

with tab4:
    st.markdown("## ⚙️ LLM Settings")

    PROVIDER_NAMES = {"ollama": "Ollama (local)", "hf": "Hugging Face", "gemini": "Gemini", "groq": "Groq"}
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### LLM Provider & Model")
        llm_provider = st.selectbox(
            "Provider", list(PROVIDER_NAMES), key="llm_provider",
            format_func=lambda p: PROVIDER_NAMES[p],
        )
        try:
            settings_info = fetch_json(f"{api_url}/api/models?provider={llm_provider}")
            settings_models = settings_info["models"]
            settings_default = settings_info.get("default")
            settings_configured = settings_info.get("configured", True)
        except Exception as e:
            st.error(f"Cannot load models for {llm_provider}: {e}")
            settings_models, settings_default, settings_configured = [], None, False

        if llm_provider == "ollama" and not settings_models:
            st.warning("No Ollama models found. Start Ollama and pull a model.")

        if settings_models:
            settings_model = st.selectbox(
                "Pulled Ollama model" if llm_provider == "ollama" else "Model", settings_models,
                index=(settings_models.index(settings_default) if settings_default in settings_models else 0),
                key=f"llm_model_{llm_provider}",
            )
        else:
            settings_model = None
            if llm_provider != "ollama" and not settings_configured:
                st.warning(f"No API key set for {PROVIDER_NAMES[llm_provider]}. Add it to .env.")

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
# TAB 5: Test Case Designer (dataset test generation)
# ============================================================================

def _job_is_finished(status: str) -> bool:
    return status in ("completed", "stopped", "failed")


def show_generation_job():
    """Progress and results for the current job.

    While the job runs, this fragment refreshes every 2 seconds. When it finishes, the
    app reruns once without the timer, so the page stops refreshing.
    """
    job_id = st.session_state.get("gen_job_id")
    if not job_id:
        return
    polling = not _job_is_finished(st.session_state.get("gen_job_status") or "")
    st.fragment(run_every=2 if polling else None)(_render_generation_job)(job_id, polling)


def _render_generation_job(job_id: str, polling: bool):
    try:
        job = requests.get(f"{api_url}/api/test-generation/{job_id}", timeout=5).json()
    except requests.RequestException as e:
        st.warning(f"Lost contact with the API while checking the job: {e}")
        return
    st.session_state["gen_job_status"] = job["status"]
    if polling and _job_is_finished(job["status"]):
        st.rerun(scope="app")  # full rerun without the timer

    model_label = job["model"] or "default (OLLAMA_MODEL)"
    st.markdown(
        f"**Status:** `{job['status']}` · **Dataset:** `{job['dataset']}` · "
        f"**Template:** `{job['template']}` · **Model:** `{model_label}`"
    )
    total = job["total"] or 0
    processed = job["done"] + job["failed"]
    if total:
        st.progress(min(processed / total, 1.0),
                    text=f"{processed}/{total} rows · {job['done']} saved · {job['failed']} failed")
    if job["status"] in ("running", "stopping"):
        if st.button("⏹ Stop after current row", key="stop_generation", disabled=job["status"] == "stopping"):
            requests.post(f"{api_url}/api/test-generation/{job_id}/stop", timeout=5)
    if job["error"]:
        st.error(job["error"])
    if job.get("out_dir"):
        st.caption(f"Saved to `{job['out_dir']}`")

    if not _job_is_finished(job["status"]):
        return

    # Fetch results once per finished job and keep them for later reruns.
    if st.session_state.get("gen_results_for") != job_id:
        try:
            response = requests.get(f"{api_url}/api/test-generation/{job_id}/results", timeout=10)
            st.session_state["gen_results"] = response.json()["results"] if response.status_code == 200 else []
        except requests.RequestException:
            st.session_state["gen_results"] = []
        st.session_state["gen_results_for"] = job_id

    results = st.session_state.get("gen_results") or []
    if not results:
        st.info("No test cases were saved for this job.")
        return
    total_cases = sum(len(r["test_cases"]) for r in results)
    st.success(f"{len(results)} requirements, {total_cases} test cases generated.")
    st.download_button(
        "⬇️ Download results (JSON)",
        data=json.dumps(results, indent=2, ensure_ascii=False),
        file_name=f"{job_id}_test_cases.json",
        mime="application/json",
    )
    for record in results:
        text = record["input"].get("requirement_text", "")
        with st.expander(f"{record['input_id']} — {text[:90]}{'…' if len(text) > 90 else ''}"):
            st.markdown(f"**Requirement:** {text}")
            for i, case in enumerate(record["test_cases"], start=1):
                st.markdown(f"{i}. {case}")


with tab5:
    st.markdown("## 🧪 Test Case Designer")
    st.caption("Pick a dataset from data/ and a prompt template. The provider and model come from "
               "LLM Settings. Results are saved under output/results/<date_time>/.")

    try:
        datasets = fetch_json(f"{api_url}/api/datasets")["datasets"]
        templates = fetch_json(f"{api_url}/api/templates")["templates"]
    except Exception as e:
        st.error(f"Cannot load datasets from the API ({e}). Start the API server first.")
        datasets, templates = [], []

    # Provider and model are chosen in the LLM Settings tab (rendered earlier in this run).
    provider = llm_provider
    model_name = settings_model

    # Type of data decides which datasets and which template are offered.
    DATA_TYPES = {
        "Requirements": ("requirements", "requirement_test_cases"),
        "Bugs": ("bugs", "bug_test_cases"),
    }
    col_type, col_ds, col_tpl = st.columns([1, 2, 1.2])
    with col_type:
        data_type = st.selectbox("Type of Data", list(DATA_TYPES), key="designer_data_type")
    type_key, template_for_type = DATA_TYPES[data_type]

    usable = [d for d in datasets if d.get("rows") is not None and d.get("type") == type_key]
    for d in datasets:
        if d.get("rows") is None:
            st.caption(f"⚠️ {d['file']} skipped: {d.get('error')}")

    if usable:
        label = {d["file"]: f"{d['file']}  ({d['rows']} rows)" for d in usable}
        with col_ds:
            dataset_file = st.selectbox("Dataset", list(label), format_func=lambda f: label[f],
                                        key=f"designer_dataset_{type_key}")
        with col_tpl:
            # Only the template for the chosen type is offered.
            template_name = st.selectbox("Template", [template_for_type], key=f"designer_template_{type_key}")
        if model_name:
            st.info(f"Provider: **{PROVIDER_NAMES[provider]}** · Model: **{model_name}** "
                    "(change in LLM Settings)")
        else:
            st.warning(f"No model selected for {PROVIDER_NAMES[provider]}. Choose one in LLM Settings.")
        limit = st.number_input(
            "Rows to process (0 = all)", min_value=0,
            value=10 if type_key == "bugs" else 0, step=1,
            help="The bugs dataset has about 11,000 reports; start with a small number.",
            key=f"designer_limit_{type_key}",
        )

        selected = next(d for d in usable if d["file"] == dataset_file)
        st.caption(f"Columns: {', '.join(selected.get('columns', []))} · "
                   f"id: `{selected['id_column']}` · text: `{selected['text_column']}`")

        if st.button("▶️ Generate test cases", type="primary", use_container_width=True,
                     disabled=not model_name):
            payload = {"dataset": dataset_file, "template": template_name, "provider": provider,
                       "model": model_name, "limit": int(limit)}
            try:
                response = requests.post(f"{api_url}/api/test-generation", json=payload, timeout=30)
                if response.status_code == 202:
                    st.session_state["gen_job_id"] = response.json()["job_id"]
                    st.session_state["gen_job_status"] = "running"  # starts the 2-second refresh
                    st.session_state.pop("gen_results_for", None)
                else:
                    st.error(response.json().get("detail", response.text))
            except requests.RequestException as e:
                st.error(f"Could not start the job: {e}")
    else:
        st.info(f"No {data_type.lower()} datasets found under data/.")

    st.markdown("### Job")
    show_generation_job()

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
