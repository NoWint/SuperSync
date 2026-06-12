import subprocess


def run_command(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        *args: Command and arguments.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance with stdout and stderr.
    """
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
    )


def run_command_optional(*args: str) -> subprocess.CompletedProcess | None:
    """Run a command, returning None if the command is not found or fails."""
    try:
        result = run_command(*args, check=False)
        if result.returncode != 0:
            return None
        return result
    except FileNotFoundError:
        return None
