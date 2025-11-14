"""CLI interface for Terminus agent."""
import asyncio
import os
import tempfile
from pathlib import Path

import typer
from typing_extensions import Annotated

from terminus.terminus_2 import Terminus2

app = typer.Typer(help="Terminus - Terminal-based AI agent for task execution")


@app.command()
def run(
    instruction: Annotated[str, typer.Argument(help="Task instruction to execute")],
    model: Annotated[str, typer.Option("--model", "-m", help="Model name to use")] = "openai/gpt-4o",
    logs_dir: Annotated[Path, typer.Option("--logs-dir", "-l", help="Directory for logs")] = Path("./terminus_logs"),
    parser: Annotated[str, typer.Option("--parser", "-p", help="Parser to use (json or xml)")] = "json",
    temperature: Annotated[float, typer.Option("--temperature", "-t", help="Sampling temperature")] = 0.7,
    max_turns: Annotated[int, typer.Option("--max-turns", help="Maximum number of turns")] = 1000000,
    api_base: Annotated[str | None, typer.Option("--api-base", help="API base URL")] = None,
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory to mount in container")] = Path.cwd(),
):
    """Run the Terminus agent with the given instruction."""
    from harbor.environments.docker.docker import DockerEnvironment
    from harbor.models.agent.context import AgentContext
    from harbor.models.environment_type import EnvironmentType
    from harbor.models.task.config import EnvironmentConfig
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

    # Create a minimal docker-compose.yaml for the environment
    env_dir = logs_dir / "environment"
    env_dir.mkdir(exist_ok=True)

    docker_compose_content = f"""version: '3.8'
services:
  main:
    image: ubuntu:22.04
    command: sleep infinity
    working_dir: /workspace
    volumes:
      - {working_dir}:/workspace
    environment:
      - OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', '')}
"""

    (env_dir / "docker-compose.yaml").write_text(docker_compose_content)

    agent = Terminus2(
        logs_dir=logs_dir,
        model_name=model,
        max_turns=max_turns,
        parser_name=parser,
        api_base=api_base,
        temperature=temperature,
    )

    # Create trial paths
    trial_paths = TrialPaths(trial_dir=logs_dir)

    # Create a Docker environment
    env_config = EnvironmentConfig(
        type=EnvironmentType.DOCKER,
        cpus=2,
        memory_mb=4096,
        storage_mb=10240,
    )

    environment = DockerEnvironment(
        environment_dir=env_dir,
        environment_name="terminus-cli",
        session_id="terminus-cli-session",
        trial_paths=trial_paths,
        task_env_config=env_config,
    )

    context = AgentContext()

    # Run the agent
    async def run_agent():
        try:
            typer.echo("\nStarting Docker environment...")
            await environment.start(force_build=False)
            typer.echo("Docker environment started")

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
            typer.echo("\nCleaning up Docker environment...")
            await environment.stop(delete=True)

    asyncio.run(run_agent())


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
