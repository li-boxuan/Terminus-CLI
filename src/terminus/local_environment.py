"""Local host environment for running commands directly on the host system."""

import asyncio
import shutil
from pathlib import Path

from harbor.environments.base import BaseEnvironment, ExecResult
from harbor.models.environment_type import EnvironmentType
from harbor.models.task.config import EnvironmentConfig
from harbor.models.trial.paths import TrialPaths


class LocalEnvironment(BaseEnvironment):
    """
    Environment that executes commands directly on the local host system.

    This is a lightweight environment that doesn't require Docker or any
    containerization. It runs commands in the local filesystem using subprocess.
    """

    def __init__(
        self,
        working_dir: Path,
        trial_paths: TrialPaths,
        task_env_config: EnvironmentConfig | None = None,
        **kwargs,
    ):
        """
        Initialize a LocalEnvironment.

        Args:
            working_dir: The working directory for command execution
            trial_paths: The trial paths for logging
            task_env_config: Optional environment configuration
        """
        # Set working_dir first, before calling super().__init__
        # because _validate_definition will be called by parent __init__
        self.working_dir = working_dir
        self._started = False

        # Create a minimal environment directory
        environment_dir = trial_paths.trial_dir / "environment"
        environment_dir.mkdir(parents=True, exist_ok=True)

        if task_env_config is None:
            task_env_config = EnvironmentConfig(
                type=EnvironmentType.DOCKER,  # Use DOCKER as a placeholder type
                cpus=1,
                memory_mb=4096,
                storage_mb=10240,
            )

        super().__init__(
            environment_dir=environment_dir,
            environment_name="local",
            session_id="local-session",
            trial_paths=trial_paths,
            task_env_config=task_env_config,
            **kwargs,
        )

    @staticmethod
    def type() -> EnvironmentType:
        """The environment type."""
        return EnvironmentType.DOCKER  # Use DOCKER as a placeholder type

    @property
    def is_mounted(self) -> bool:
        """Local environment has direct filesystem access."""
        return True

    def _validate_definition(self):
        """Validate that the working directory exists."""
        if not self.working_dir.exists():
            raise FileNotFoundError(f"Working directory does not exist: {self.working_dir}")

    async def start(self, force_build: bool = False):
        """Start the environment (no-op for local)."""
        self.logger.info(f"Using local environment with working directory: {self.working_dir}")
        self._started = True

    async def stop(self, delete: bool = False):
        """Stop the environment (no-op for local)."""
        self.logger.info("Stopping local environment")
        self._started = False

    async def exec(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_sec: int | None = None,
    ) -> ExecResult:
        """
        Execute a command on the local host.

        Args:
            command: The command to execute
            cwd: The working directory (defaults to self.working_dir)
            env: Additional environment variables
            timeout_sec: Timeout in seconds

        Returns:
            ExecResult with stdout, stderr, and return code
        """
        if cwd is None:
            cwd = str(self.working_dir)

        self.logger.debug(f"Executing: {command} in {cwd}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                return ExecResult(
                    stdout="",
                    stderr=f"Command timed out after {timeout_sec} seconds",
                    return_code=-1,
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return_code = process.returncode or 0

            return ExecResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
            )

        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            return ExecResult(
                stdout="",
                stderr=str(e),
                return_code=-1,
            )

    async def upload_file(self, source_path: Path | str, target_path: str):
        """
        Copy a file to the target path (local filesystem copy).

        Args:
            source_path: Source file path
            target_path: Target file path
        """
        source = Path(source_path)
        target = Path(target_path)

        # Make absolute if not already
        if not target.is_absolute():
            target = self.working_dir / target

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        self.logger.debug(f"Copied {source} to {target}")

    async def upload_dir(self, source_dir: Path | str, target_dir: str):
        """
        Copy a directory to the target path.

        Args:
            source_dir: Source directory path
            target_dir: Target directory path
        """
        source = Path(source_dir)
        target = Path(target_dir)

        if not target.is_absolute():
            target = self.working_dir / target

        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        self.logger.debug(f"Copied directory {source} to {target}")

    async def download_file(self, source_path: str, target_path: Path | str):
        """
        Copy a file from the environment (local filesystem copy).

        Args:
            source_path: Source file path in environment
            target_path: Target local file path
        """
        source = Path(source_path)
        if not source.is_absolute():
            source = self.working_dir / source

        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        self.logger.debug(f"Downloaded {source} to {target}")

    async def download_dir(self, source_dir: str, target_dir: Path | str):
        """
        Copy a directory from the environment.

        Args:
            source_dir: Source directory path in environment
            target_dir: Target local directory path
        """
        source = Path(source_dir)
        if not source.is_absolute():
            source = self.working_dir / source

        target = Path(target_dir)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        self.logger.debug(f"Downloaded directory {source} to {target}")

    async def kill(self):
        """Kill the environment (no-op for local)."""
        await self.stop()

    async def restart(self):
        """Restart the environment (no-op for local)."""
        await self.stop()
        await self.start()
