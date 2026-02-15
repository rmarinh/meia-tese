"""TestForge Streamlit Web UI."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import streamlit as st

# Ensure testforge is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from testforge.orchestration.engine import PipelineRequest, run_pipeline


def main():
    st.set_page_config(
        page_title="TestForge",
        page_icon="*",
        layout="wide",
    )

    st.title("TestForge")
    st.caption("Automated test generation using multi-agent systems and LLMs")

    # Sidebar config
    with st.sidebar:
        st.header("Configuration")
        base_url = st.text_input("Base URL", value="http://localhost:5000")
        app_description = st.text_area("Application Description", height=80)
        num_tests = st.slider("Number of tests to generate", 1, 50, 10)
        execute_tests = st.checkbox("Execute generated tests", value=False)

        st.divider()
        st.header("LLM Settings")
        llm_model = st.text_input("Model", value="gpt-4o")
        llm_api_key = st.text_input("API Key", type="password")

        if llm_api_key:
            import os
            os.environ["TESTFORGE_LLM_API_KEY"] = llm_api_key
            os.environ["TESTFORGE_LLM_MODEL"] = llm_model

    # Main tabs
    tab_golden, tab_observer, tab_combined = st.tabs([
        "Golden Examples",
        "Observer Mode",
        "Combined Mode",
    ])

    with tab_golden:
        _golden_tab(base_url, app_description, num_tests, execute_tests)

    with tab_observer:
        _observer_tab(base_url, app_description, num_tests, execute_tests)

    with tab_combined:
        _combined_tab(base_url, app_description, num_tests, execute_tests)


def _golden_tab(base_url: str, app_description: str, num_tests: int, execute_tests: bool):
    st.header("Golden Examples Pipeline")
    st.write("Upload reference test files and generate new tests that follow the same patterns.")

    uploaded_files = st.file_uploader(
        "Upload golden test files (.py)",
        type=["py"],
        accept_multiple_files=True,
        key="golden_files",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Tests", key="golden_generate", type="primary"):
            if not uploaded_files:
                st.error("Please upload at least one golden test file.")
                return

            source_codes = []
            for f in uploaded_files:
                source_codes.append(f.read().decode("utf-8"))

            request = PipelineRequest(
                mode="golden",
                golden_source_codes=source_codes,
                base_url=base_url,
                app_description=app_description,
                num_tests=num_tests,
                execute_tests=execute_tests,
            )

            with st.spinner("Running Golden Examples pipeline..."):
                result = asyncio.run(run_pipeline(request))

            _display_results(result)

    # Show uploaded files preview
    if uploaded_files:
        with st.expander("Preview uploaded files"):
            for f in uploaded_files:
                st.subheader(f.name)
                f.seek(0)
                st.code(f.read().decode("utf-8"), language="python")


def _observer_tab(base_url: str, app_description: str, num_tests: int, execute_tests: bool):
    st.header("Observer Pipeline")
    st.write("Import captured HTTP traffic (HAR file or JSON exchanges) to generate tests.")

    input_mode = st.radio(
        "Input mode",
        ["HAR File", "JSON Exchanges", "Manual Endpoints"],
        key="observer_input_mode",
    )

    if input_mode == "HAR File":
        har_file = st.file_uploader("Upload HAR file", type=["har", "json"], key="har_file")
        app_name = st.text_input("Application name", value="app", key="obs_app_name")

        if st.button("Generate Tests", key="observer_generate", type="primary"):
            if not har_file:
                st.error("Please upload a HAR file.")
                return

            import tempfile

            content = har_file.read()
            with tempfile.NamedTemporaryFile(suffix=".har", delete=False, mode="wb") as f:
                f.write(content)
                har_path = f.name

            request = PipelineRequest(
                mode="observer",
                har_file_path=har_path,
                app_name=app_name,
                base_url=base_url,
                app_description=app_description,
                num_tests=num_tests,
                execute_tests=execute_tests,
            )

            with st.spinner("Running Observer pipeline..."):
                result = asyncio.run(run_pipeline(request))

            _display_results(result)

    elif input_mode == "JSON Exchanges":
        exchanges_json = st.text_area(
            "Paste HTTP exchanges JSON",
            height=300,
            placeholder='[{"method": "GET", "url": "http://localhost:5000/api/users", ...}]',
            key="exchanges_json",
        )

        if st.button("Generate Tests", key="observer_json_generate", type="primary"):
            if not exchanges_json.strip():
                st.error("Please provide HTTP exchanges JSON.")
                return

            try:
                exchanges = json.loads(exchanges_json)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                return

            request = PipelineRequest(
                mode="observer",
                captured_exchanges=exchanges,
                base_url=base_url,
                app_description=app_description,
                num_tests=num_tests,
                execute_tests=execute_tests,
            )

            with st.spinner("Running Observer pipeline..."):
                result = asyncio.run(run_pipeline(request))

            _display_results(result)

    elif input_mode == "Manual Endpoints":
        st.write("Define endpoints manually:")
        endpoints_yaml = st.text_area(
            "Endpoints (one per line: METHOD /path description)",
            height=200,
            placeholder="GET /api/users List all users\nPOST /api/users Create a new user\nGET /api/users/{id} Get user by ID",
            key="manual_endpoints",
        )

        if st.button("Generate Tests", key="observer_manual_generate", type="primary"):
            if not endpoints_yaml.strip():
                st.error("Please define at least one endpoint.")
                return

            exchanges = []
            for line in endpoints_yaml.strip().split("\n"):
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    method, path = parts[0], parts[1]
                    exchanges.append({
                        "method": method,
                        "url": f"{base_url}{path}",
                        "path": path,
                        "status_code": 200,
                        "request_body": None,
                        "response_body": {},
                        "response_content_type": "application/json",
                    })

            request = PipelineRequest(
                mode="observer",
                captured_exchanges=exchanges,
                base_url=base_url,
                app_description=app_description,
                num_tests=num_tests,
                execute_tests=execute_tests,
            )

            with st.spinner("Running Observer pipeline..."):
                result = asyncio.run(run_pipeline(request))

            _display_results(result)


def _combined_tab(base_url: str, app_description: str, num_tests: int, execute_tests: bool):
    st.header("Combined Mode")
    st.write("Use golden examples for style + observed traffic for endpoint discovery.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Golden Examples (for style)")
        golden_files = st.file_uploader(
            "Upload golden test files",
            type=["py"],
            accept_multiple_files=True,
            key="combined_golden",
        )

    with col2:
        st.subheader("Traffic (for endpoints)")
        har_file = st.file_uploader("Upload HAR file", type=["har", "json"], key="combined_har")

    if st.button("Generate Tests", key="combined_generate", type="primary"):
        source_codes = []
        if golden_files:
            for f in golden_files:
                source_codes.append(f.read().decode("utf-8"))

        har_path = None
        if har_file:
            import tempfile

            content = har_file.read()
            with tempfile.NamedTemporaryFile(suffix=".har", delete=False, mode="wb") as f:
                f.write(content)
                har_path = f.name

        request = PipelineRequest(
            mode="combined",
            golden_source_codes=source_codes,
            har_file_path=har_path,
            base_url=base_url,
            app_description=app_description,
            num_tests=num_tests,
            execute_tests=execute_tests,
        )

        with st.spinner("Running Combined pipeline..."):
            result = asyncio.run(run_pipeline(request))

        _display_results(result)


def _display_results(result):
    """Display pipeline results."""
    if not result.success:
        st.error("Pipeline failed!")
        for err in result.errors:
            st.error(err)
        return

    st.success("Pipeline completed successfully!")

    if result.summary:
        st.info(result.summary)

    # Show generated test code
    test_file = ""
    if result.golden_result and result.golden_result.get("test_file"):
        test_file = result.golden_result["test_file"]
    elif result.observer_result and result.observer_result.get("test_file"):
        test_file = result.observer_result["test_file"]

    if test_file:
        st.subheader("Generated Tests")
        st.code(test_file, language="python")

        st.download_button(
            "Download test file",
            data=test_file,
            file_name="test_generated.py",
            mime="text/x-python",
        )

    if result.test_file_path:
        st.caption(f"Test file saved to: {result.test_file_path}")

    # Show raw LLM response in expander
    raw = ""
    if result.golden_result:
        raw = result.golden_result.get("raw_response", "")
    elif result.observer_result:
        raw = result.observer_result.get("raw_response", "")
    if raw:
        with st.expander("Raw LLM Response"):
            st.text(raw)


if __name__ == "__main__":
    main()
