# Terminus

Terminus is an agent for terminal-based task execution. It integrates with Harbor for agent evaluation and task execution.

## Installation

### Prerequisites

- Python >=3.12
- Harbor framework installed

### Install from local path

For local development:

```bash
pip install -e /path/to/terminus
```

## Usage

### Command Line Interface

Terminus provides a CLI for quick testing and demonstration:

```bash
# Basic usage
terminus "Create a file hello.txt with Hello World"

# With options
terminus "Create a file hello.txt" \
  --model openai/gpt-4o \
  --logs-dir ./logs \
  --parser json \
  --temperature 0.7

# Show help
terminus --help
```

**Note:** The CLI is primarily for testing. For full functionality, Terminus requires integration with Harbor (see below).

### Usage with Harbor

Terminus is designed to work as an external agent with Harbor. You can use it in several ways:

### Option 1: Using import path (Recommended)

When configuring your Harbor task, use the import path to load the Terminus agent:

```yaml
agent:
  import_path: "terminus:Terminus2"
  model_name: "anthropic/claude-sonnet-4"
  kwargs:
    parser_name: "json"  # or "xml"
    temperature: 0.7
    max_turns: 100
    enable_summarize: true
```

Or in Python:

```python
from harbor import AgentFactory
from pathlib import Path

agent = AgentFactory.create_agent_from_import_path(
    import_path="terminus:Terminus2",
    logs_dir=Path("./logs"),
    model_name="anthropic/claude-sonnet-4",
    parser_name="json",
    temperature=0.7,
)
```

### Option 2: Direct instantiation

```python
from terminus import Terminus2
from pathlib import Path

agent = Terminus2(
    logs_dir=Path("./logs"),
    model_name="anthropic/claude-sonnet-4",
    parser_name="json",  # or "xml"
    temperature=0.7,
    max_turns=100,
    enable_summarize=True,
)
```

## Configuration Options

- `model_name`: The LLM model to use (required)
- `parser_name`: Response format - "json" or "xml" (default: "json")
- `temperature`: Sampling temperature (default: 0.7)
- `max_turns`: Maximum number of agent turns (default: 1000000)
- `enable_summarize`: Enable context summarization when limits are reached (default: True)
- `api_base`: Custom API base URL (optional)
- `collect_rollout_details`: Collect detailed token-level rollout data (default: False)
