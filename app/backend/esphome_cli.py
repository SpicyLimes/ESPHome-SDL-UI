import asyncio
from pathlib import Path
from typing import Optional, Tuple, List
from .config import ESPHOME_PATH
from .logger import setup_logger

logger = setup_logger(__name__)

class ESPHomeCLI:
    def __init__(self, esphome_path: str = ESPHOME_PATH):
        self.esphome_bin = esphome_path
        self.current_process: Optional[asyncio.subprocess.Process] = None

    def _get_command_prefix(self) -> List[str]:
        return [str(self.esphome_bin)]

    async def validate_config(self, config_path: Path, timeout: int = 120) -> Tuple[bool, str]:
        try:
            cmd = self._get_command_prefix() + ["config", str(config_path)]

            logger.info(f"Validating config: {config_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"Validation timed out after {timeout} seconds"
                logger.error(error_msg)
                return False, error_msg

            output = stdout.decode() + stderr.decode()

            success = process.returncode == 0

            if success:
                logger.info(f"Config validation successful: {config_path}")
            else:
                logger.warning(f"Config validation failed: {config_path}")

            return success, output

        except Exception as e:
            error_msg = f"Failed to validate config: {e}"
            logger.error(error_msg)
            return False, error_msg

    async def compile_config(self, config_path: Path, timeout: int = 600) -> Tuple[bool, str]:
        try:
            cmd = self._get_command_prefix() + ["compile", str(config_path)]

            logger.info(f"Compiling config: {config_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"Compilation timed out after {timeout} seconds"
                logger.error(error_msg)
                return False, error_msg

            output = stdout.decode() + stderr.decode()

            success = process.returncode == 0

            if success:
                logger.info(f"Config compilation successful: {config_path}")
            else:
                logger.warning(f"Config compilation failed: {config_path}")

            return success, output

        except Exception as e:
            error_msg = f"Failed to compile config: {e}"
            logger.error(error_msg)
            return False, error_msg

    async def run_config(self, config_path: Path) -> Tuple[bool, str]:
        try:
            cmd = self._get_command_prefix() + ["run", str(config_path)]

            logger.info(f"Running config: {config_path}")

            self.current_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await asyncio.sleep(2)

            if self.current_process.returncode is not None:
                stdout, stderr = await self.current_process.communicate()
                output = stdout.decode() + stderr.decode()
                success = self.current_process.returncode == 0
                return success, output

            return True, "SDL2 display started successfully. Process running in background."

        except Exception as e:
            error_msg = f"Failed to run config: {e}"
            logger.error(error_msg)
            return False, error_msg

    async def stop_current_process(self) -> bool:
        try:
            if self.current_process and self.current_process.returncode is None:
                self.current_process.terminate()
                await asyncio.sleep(1)

                if self.current_process.returncode is None:
                    self.current_process.kill()
                    await self.current_process.wait()

                logger.info("SDL2 process stopped")
                self.current_process = None
                return True

            # Process already stopped or doesn't exist
            self.current_process = None
            return False

        except Exception as e:
            logger.error(f"Failed to stop process: {e}")
            self.current_process = None
            return False

    def is_process_running(self) -> bool:
        """Check if the SDL2 process is currently running."""
        if self.current_process is None:
            return False
        return self.current_process.returncode is None

    async def get_version(self) -> Tuple[bool, str]:
        try:
            cmd = self._get_command_prefix() + ["version"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode().strip()

            return process.returncode == 0, output

        except Exception as e:
            return False, str(e)

    async def clean_build(self, config_path: Path) -> Tuple[bool, str]:
        try:
            cmd = self._get_command_prefix() + ["clean", str(config_path)]

            logger.info(f"Cleaning build files: {config_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode() + stderr.decode()

            success = process.returncode == 0

            if success:
                logger.info(f"Build files cleaned: {config_path}")

            return success, output

        except Exception as e:
            error_msg = f"Failed to clean build: {e}"
            logger.error(error_msg)
            return False, error_msg
