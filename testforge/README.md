# TestForge

Automated test generation platform using multi-agent systems and LLMs.

## Quick Start

```bash
pip install -e ".[dev]"

# Set your LLM API key
export TESTFORGE_LLM_API_KEY="your-key"

# Generate tests from golden examples
testforge generate examples/flask_api_tests/test_users_golden_*.py --no-execute

# Start the web UI
testforge ui

# Start the API server
testforge serve
```

## Architecture

TestForge uses 6 specialized agents in two pipelines:

**Golden Examples Pipeline**: Analyzer → Generator → Executor → Validator
**Observer Pipeline**: Observer → Mapper → Generator → Executor → Validator
