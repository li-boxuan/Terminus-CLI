"""CLI interface for Terminus agent."""
import asyncio
import shutil
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from terminus.local_environment import LocalEnvironment
from terminus.terminus import Terminus

app = typer.Typer(help="Terminus - Terminal-based AI agent for task execution")


def check_tmux_available() -> bool:
    """Check if tmux is available on the system."""
    return shutil.which("tmux") is not None


@app.command()
def run(
    instruction: Annotated[str, typer.Argument(help="Task instruction to execute")],
    model: Annotated[str, typer.Option("--model", "-m", help="Model name to use")] = "openai/gpt-4o",
    logs_dir: Annotated[Path, typer.Option("--logs-dir", "-l", help="Directory for logs")] = Path("./terminus_logs"),
    parser: Annotated[str, typer.Option("--parser", "-p", help="Parser to use (json or xml)")] = "json",
    temperature: Annotated[float, typer.Option("--temperature", "-t", help="Sampling temperature")] = 0.7,
    max_turns: Annotated[int, typer.Option("--max-turns", help="Maximum number of turns")] = 1000000,
    api_base: Annotated[str | None, typer.Option("--api-base", help="API base URL")] = None,
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory for task execution")] = Path.cwd(),
):
    """Run the Terminus agent with the given instruction."""
    # Check if tmux is available
    if not check_tmux_available():
        typer.echo(
            "✗ Error: tmux is not installed or not available in PATH.\n"
            "\n"
            "Terminus requires tmux to manage terminal sessions.\n"
            "\n"
            "To install tmux:\n"
            "  - macOS: brew install tmux\n"
            "  - Ubuntu/Debian: sudo apt-get install tmux\n"
            "  - Fedora: sudo dnf install tmux\n"
            "  - Arch: sudo pacman -S tmux\n",
            err=True,
        )
        sys.exit(1)

    from harbor.models.agent.context import AgentContext
    from harbor.models.trial.paths import TrialPaths

    typer.echo(f"Starting Terminus agent...")
    typer.echo(f"Model: {model}")
    typer.echo(f"Parser: {parser}")
    typer.echo(f"Logs directory: {logs_dir}")
    typer.echo(f"Working directory: {working_dir}")
    typer.echo(f"Instruction: {instruction}")

    # Create logs directory if it doesn't exist
    logs_dir = logs_dir.resolve()
    logs_dir.mkdir(parents=True, exist_ok=True)

    working_dir = working_dir.resolve()

    agent = Terminus(
        logs_dir=logs_dir,
        model_name=model,
        max_turns=max_turns,
        parser_name=parser,
        api_base=api_base,
        temperature=temperature,
    )

    # Create trial paths
    trial_paths = TrialPaths(trial_dir=logs_dir)

    # Create a local environment (no Docker needed!)
    environment = LocalEnvironment(
        working_dir=working_dir,
        trial_paths=trial_paths,
    )

    context = AgentContext()

    # Run the agent
    async def run_agent():
        try:
            typer.echo("\nStarting local environment...")
            await environment.start(force_build=False)
            typer.echo("Environment ready")

            typer.echo("\nSetting up agent...")
            await agent.setup(environment)

            typer.echo(f"\nRunning agent on task: {instruction}\n")
            await agent.run(instruction, environment, context)

            typer.echo("\n" + "="*50)
            typer.echo("✓ Task completed!")
            if context.cost_usd:
                typer.echo(f"Total cost: ${context.cost_usd:.4f}")
            if context.metadata:
                typer.echo(f"Turns: {context.metadata.get('n_episodes', 0)}")
            typer.echo("="*50)
        except Exception as e:
            typer.echo(f"\n✗ Error: {e}", err=True)
            raise
        finally:
            typer.echo("\nCleaning up...")
            await agent.teardown()
            await environment.stop(delete=False)

    asyncio.run(run_agent())


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
