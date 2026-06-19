import sys
from supersync.utils.run import run_command


def test_run_command_success():
    result = run_command(sys.executable, "-c", "print('hello')")
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_run_command_failure():
    import pytest
    with pytest.raises(FileNotFoundError):
        run_command("nonexistent_command_xyz")
