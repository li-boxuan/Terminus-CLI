# Terminus CLI

Terminus CLI is a CLI agent for terminal-based task execution. It can be used as a standalone tool, although
it was primarily designed as a research-preview agent for evaluating the abilities of language models to
power autonomous agents in the terminal.

Note that Terminus CLI is a fork of [Terminus-2 agent](https://www.tbench.ai/terminus), which is a built-in agent in terminal-bench.
Terminus CLI 2.0.0 shows slightly better performance than Terminus-2 agent with openai/gpt-5 model on terminal-bench@2.0.0 benchmark.
Different from Terminus-2, which by design runs its control logic outside task's container, Terminus CLI is a standalone library
that runs entirely inside task's container.

## Installation

### Prerequisites

- Python >=3.12
- tmux (required for terminal session management)

### Installing tmux

Terminus requires tmux to manage terminal sessions. Install it using your system's package manager:

**macOS:**
```bash
brew install tmux
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tmux
```

**Fedora:**
```bash
sudo dnf install tmux
```

**Arch Linux:**
```bash
sudo pacman -S tmux
```

### Install Terminus

```bash tab="uv"
uv tool install terminus-ai
```
or
```bash tab="pip"
pip install terminus-ai
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

**Note:**
- The CLI runs directly on your local system using tmux (no Docker required)
- Perfect for quick tasks, testing, and automation

### Programmatic Usage

You can also use Terminus programmatically in Python:

```python
from terminus import Terminus
from pathlib import Path

agent = Terminus(
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
