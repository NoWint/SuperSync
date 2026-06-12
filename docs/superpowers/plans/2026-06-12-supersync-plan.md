# SuperSync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that scans a developer's macOS environment, encrypts it into a portable `.supersync` file, and restores it on another machine.

**Architecture:** Three-phase pipeline — Scanner (probe environment) → Manifest+Crypto (serialize & encrypt) → Provisioner (orchestrated restore). Declarative YAML manifest with AES-256-GCM encryption. CLI built with Typer + Rich.

**Tech Stack:** Python 3.11+, typer, pydantic, cryptography, rich, pyyaml, pytest

---

## File Structure

```
SuperSync/
├── src/supersync/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point (Typer app)
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── base.py               # ScannerBase, ScanResult, Item
│   │   ├── brew.py               # Homebrew scanner
│   │   ├── pip_scanner.py        # pip scanner (renamed to avoid stdlib clash)
│   │   ├── npm.py                # npm scanner
│   │   ├── env_vars.py           # Environment variable scanner
│   │   ├── dotfiles.py           # Dotfiles scanner
│   │   └── ide.py                # VS Code scanner
│   ├── manifest/
│   │   ├── __init__.py
│   │   ├── schema.py             # Pydantic models for Manifest
│   │   ├── serializer.py         # YAML serialization
│   │   └── crypto.py             # AES-256-GCM encrypt/decrypt
│   ├── provisioner/
│   │   ├── __init__.py
│   │   ├── dependency.py         # Topological sort
│   │   ├── installer.py          # Package installers
│   │   ├── conflict.py           # Conflict detection & resolution
│   │   └── engine.py             # Orchestration engine
│   └── utils/
│       ├── __init__.py
│       └── run.py                # Subprocess runner helper
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_scanner/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_brew.py
│   │   ├── test_pip.py
│   │   ├── test_npm.py
│   │   ├── test_env_vars.py
│   │   ├── test_dotfiles.py
│   │   └── test_ide.py
│   ├── test_manifest/
│   │   ├── __init__.py
│   │   ├── test_schema.py
│   │   ├── test_serializer.py
│   │   └── test_crypto.py
│   ├── test_provisioner/
│   │   ├── __init__.py
│   │   ├── test_dependency.py
│   │   ├── test_installer.py
│   │   ├── test_conflict.py
│   │   └── test_engine.py
│   └── test_cli.py
├── pyproject.toml
└── docs/
    └── superpowers/
        ├── specs/2026-06-12-supersync-design.md
        └── plans/2026-06-12-supersync-plan.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/supersync/__init__.py`
- Create: `src/supersync/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "supersync"
version = "0.1.0"
description = "Cross-device development environment migration tool"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12.0",
    "pydantic>=2.0",
    "cryptography>=42.0",
    "rich>=13.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]

[project.scripts]
supersync = "supersync.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/supersync"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package init**

`src/supersync/__init__.py`:
```python
"""SuperSync - Cross-device development environment migration tool."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create CLI skeleton**

`src/supersync/cli.py`:
```python
import typer

app = typer.Typer(
    name="supersync",
    help="Cross-device development environment migration tool.",
    no_args_is_help=True,
)


@app.command()
def scan(
    output: str = typer.Option("env.supersync", "--output", "-o", help="Output file path"),
    skip_sensitive: bool = typer.Option(False, "--skip-sensitive", help="Skip all sensitive items"),
    include_all_sensitive: bool = typer.Option(False, "--include-all-sensitive", help="Include all sensitive items"),
) -> None:
    """Scan current development environment and generate encrypted snapshot."""
    typer.echo("Scanning environment...")


@app.command()
def restore(
    file: str = typer.Argument(..., help="Path to .supersync file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, do not execute"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm all prompts"),
) -> None:
    """Restore development environment from a .supersync file."""
    typer.echo(f"Restoring from {file}...")


@app.command()
def inspect(
    file: str = typer.Argument(..., help="Path to .supersync file"),
) -> None:
    """Decrypt and display the contents of a .supersync file."""
    typer.echo(f"Inspecting {file}...")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create test conftest**

`tests/__init__.py`:
```python
```

`tests/conftest.py`:
```python
import pytest
```

- [ ] **Step 5: Install project and verify CLI works**

Run: `cd /Users/xiatian/Desktop/SuperSync && pip install -e ".[dev]"`
Run: `supersync --help`
Expected: CLI help text displayed with scan, restore, inspect commands

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffolding with CLI skeleton"
```

---

### Task 2: Scanner Base Class and Data Models

**Files:**
- Create: `src/supersync/scanner/__init__.py`
- Create: `src/supersync/scanner/base.py`
- Create: `tests/test_scanner/__init__.py`
- Create: `tests/test_scanner/test_base.py`

- [ ] **Step 1: Write failing test for ScanResult and ScannerBase**

`tests/test_scanner/__init__.py`:
```python
```

`tests/test_scanner/test_base.py`:
```python
from supersync.scanner.base import Item, ScanResult, ScannerBase


class TestItem:
    def test_create_item(self):
        item = Item(name="git", version="2.45.0", source="brew")
        assert item.name == "git"
        assert item.version == "2.45.0"
        assert item.source == "brew"
        assert item.sensitive is False

    def test_create_sensitive_item(self):
        item = Item(name="id_rsa", path="~/.ssh/id_rsa", sensitive=True, source="dotfiles")
        assert item.sensitive is True
        assert item.path == "~/.ssh/id_rsa"


class TestScanResult:
    def test_create_scan_result(self):
        items = [Item(name="git", version="2.45.0", source="brew")]
        result = ScanResult(source="brew", items=items, sensitive=[], errors=[])
        assert result.source == "brew"
        assert len(result.items) == 1
        assert len(result.errors) == 0

    def test_scan_result_with_errors(self):
        result = ScanResult(source="npm", items=[], sensitive=[], errors=["npm not found"])
        assert len(result.errors) == 1


class TestScannerBase:
    def test_cannot_instantiate_directly(self):
        import pytest
        with pytest.raises(TypeError):
            ScannerBase()

    def test_subclass_must_implement_scan(self):
        class IncompleteScanner(ScannerBase):
            pass

        import pytest
        with pytest.raises(TypeError):
            IncompleteScanner()

    def test_subclass_with_scan_works(self):
        class DummyScanner(ScannerBase):
            def scan(self) -> ScanResult:
                return ScanResult(source="dummy", items=[], sensitive=[], errors=[])

        scanner = DummyScanner()
        result = scanner.scan()
        assert result.source == "dummy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_base.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement ScannerBase, Item, ScanResult**

`src/supersync/scanner/__init__.py`:
```python
from supersync.scanner.base import Item, ScanResult, ScannerBase

__all__ = ["Item", "ScanResult", "ScannerBase"]
```

`src/supersync/scanner/base.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    """A single scanned item (package, file, env var, etc.)."""
    name: str
    source: str
    version: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    sensitive: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class ScanResult:
    """Result from a single scanner."""
    source: str
    items: list[Item]
    sensitive: list[Item]
    errors: list[str]


class ScannerBase(ABC):
    """Base class for all environment scanners."""

    @abstractmethod
    def scan(self) -> ScanResult:
        """Scan the environment and return results."""
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/ tests/test_scanner/
git commit -m "feat: scanner base class with Item and ScanResult data models"
```

---

### Task 3: Subprocess Runner Utility

**Files:**
- Create: `src/supersync/utils/__init__.py`
- Create: `src/supersync/utils/run.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write failing test**

`tests/test_utils.py`:
```python
from supersync.utils.run import run_command


def test_run_command_success():
    result = run_command("echo", "hello")
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_run_command_failure():
    import pytest
    with pytest.raises(FileNotFoundError):
        run_command("nonexistent_command_xyz")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement run_command**

`src/supersync/utils/__init__.py`:
```python
```

`src/supersync/utils/run.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_utils.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/utils/ tests/test_utils.py
git commit -m "feat: subprocess runner utility"
```

---

### Task 4: Brew Scanner

**Files:**
- Create: `src/supersync/scanner/brew.py`
- Create: `tests/test_scanner/test_brew.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_brew.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.scanner.brew import BrewScanner
from supersync.scanner.base import ScanResult


def test_brew_scan_parses_formula_and_cask():
    scanner = BrewScanner()

    mock_list_output = MagicMock()
    mock_list_output.stdout = "git\nnode\n"

    mock_leaves_output = MagicMock()
    mock_leaves_output.stdout = "git\nnode\n"

    mock_info_output = MagicMock()
    mock_info_output.stdout = '{"formulae":[{"name":"git","installed":[{"version":"2.45.0"}]},{"name":"node","installed":[{"version":"22.2.0"}]}],"casks":[]}'

    def mock_run(*args, **kwargs):
        cmd = args[0]
        if "list" in cmd:
            return mock_list_output
        if "leaves" in cmd:
            return mock_leaves_output
        if "info" in cmd:
            return mock_info_output
        return MagicMock(stdout="")

    with patch("supersync.scanner.brew.run_command", side_effect=mock_run):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "brew"
    assert len(result.items) > 0
    assert any(item.name == "git" for item in result.items)


def test_brew_scan_handles_brew_not_found():
    scanner = BrewScanner()

    with patch("supersync.scanner.brew.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "brew"
    assert len(result.items) == 0
    assert len(result.errors) == 1
    assert "not found" in result.errors[0].lower() or "brew" in result.errors[0].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_brew.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement BrewScanner**

`src/supersync/scanner/brew.py`:
```python
import json

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class BrewScanner(ScannerBase):
    """Scans Homebrew for installed formulae and casks."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        errors: list[str] = []

        # Check if brew is available
        brew_check = run_command_optional("brew", "--version")
        if brew_check is None:
            return ScanResult(
                source="brew",
                items=[],
                sensitive=[],
                errors=["Homebrew not found on this system"],
            )

        try:
            # Get installed formulae and casks with version info
            info_result = run_command("brew", "info", "--json=v2", "--installed")
            info_data = json.loads(info_result.stdout)

            for formula in info_data.get("formulae", []):
                name = formula["name"]
                versions = formula.get("installed", [])
                version = versions[0]["version"] if versions else "unknown"
                items.append(Item(name=name, version=version, source="brew", extra={"type": "formula"}))

            for cask in info_data.get("casks", []):
                name = cask["name"]
                version = cask.get("version", "unknown")
                items.append(Item(name=name, version=version, source="brew", extra={"type": "cask"}))

        except Exception as e:
            errors.append(f"Failed to scan Homebrew: {e}")

        return ScanResult(source="brew", items=items, sensitive=[], errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_brew.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/brew.py tests/test_scanner/test_brew.py
git commit -m "feat: Homebrew scanner"
```

---

### Task 5: Pip Scanner

**Files:**
- Create: `src/supersync/scanner/pip_scanner.py`
- Create: `tests/test_scanner/test_pip.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_pip.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.scanner.pip_scanner import PipScanner
from supersync.scanner.base import ScanResult


def test_pip_scan_parses_packages():
    scanner = PipScanner()

    mock_result = MagicMock()
    mock_result.stdout = '[{"name":"requests","version":"2.32.0"},{"name":"flask","version":"3.0.0"}]'

    with patch("supersync.scanner.pip_scanner.run_command", return_value=mock_result):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "pip"
    assert len(result.items) == 2
    assert result.items[0].name == "requests"
    assert result.items[0].version == "2.32.0"


def test_pip_scan_handles_pip_not_found():
    scanner = PipScanner()

    with patch("supersync.scanner.pip_scanner.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "pip"
    assert len(result.items) == 0
    assert len(result.errors) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_pip.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement PipScanner**

`src/supersync/scanner/pip_scanner.py`:
```python
import json

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class PipScanner(ScannerBase):
    """Scans pip for globally installed packages."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        errors: list[str] = []

        pip_check = run_command_optional("pip", "--version")
        if pip_check is None:
            return ScanResult(
                source="pip",
                items=[],
                sensitive=[],
                errors=["pip not found on this system"],
            )

        try:
            result = run_command("pip", "list", "--format=json")
            packages = json.loads(result.stdout)

            for pkg in packages:
                items.append(Item(
                    name=pkg["name"],
                    version=pkg["version"],
                    source="pip",
                ))

        except Exception as e:
            errors.append(f"Failed to scan pip: {e}")

        return ScanResult(source="pip", items=items, sensitive=[], errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_pip.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/pip_scanner.py tests/test_scanner/test_pip.py
git commit -m "feat: pip scanner"
```

---

### Task 6: Npm Scanner

**Files:**
- Create: `src/supersync/scanner/npm.py`
- Create: `tests/test_scanner/test_npm.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_npm.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.scanner.npm import NpmScanner
from supersync.scanner.base import ScanResult


def test_npm_scan_parses_global_packages():
    scanner = NpmScanner()

    mock_result = MagicMock()
    mock_result.stdout = '{"dependencies":{"typescript":{"version":"5.5.0"},"eslint":{"version":"9.0.0"}}}'

    with patch("supersync.scanner.npm.run_command", return_value=mock_result):
        with patch("supersync.scanner.npm.run_command_optional", return_value=MagicMock(stdout="")):
            result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "npm"
    assert len(result.items) == 2
    assert result.items[0].name == "typescript"


def test_npm_scan_detects_npmrc_token_as_sensitive():
    scanner = NpmScanner()

    mock_list = MagicMock()
    mock_list.stdout = '{"dependencies":{}}'

    mock_npmrc = MagicMock()
    mock_npmrc.return_value = "//registry.npmjs.org/:_authToken=secret123\n"

    with patch("supersync.scanner.npm.run_command", return_value=mock_list):
        with patch("supersync.scanner.npm.run_command_optional", return_value=MagicMock(stdout="")):
            with patch("pathlib.Path.read_text", return_value="//registry.npmjs.org/:_authToken=secret123\n"):
                with patch("pathlib.Path.exists", return_value=True):
                    result = scanner.scan()

    assert len(result.sensitive) > 0
    assert any("npmrc" in s.name.lower() or "token" in s.name.lower() for s in result.sensitive)


def test_npm_scan_handles_npm_not_found():
    scanner = NpmScanner()

    with patch("supersync.scanner.npm.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "npm"
    assert len(result.items) == 0
    assert len(result.errors) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_npm.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement NpmScanner**

`src/supersync/scanner/npm.py`:
```python
import json
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional


class NpmScanner(ScannerBase):
    """Scans npm for globally installed packages and .npmrc tokens."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        npm_check = run_command_optional("npm", "--version")
        if npm_check is None:
            return ScanResult(
                source="npm",
                items=[],
                sensitive=[],
                errors=["npm not found on this system"],
            )

        try:
            result = run_command("npm", "list", "-g", "--json")
            data = json.loads(result.stdout)

            for name, info in data.get("dependencies", {}).items():
                version = info.get("version", "unknown")
                items.append(Item(
                    name=name,
                    version=version,
                    source="npm",
                    extra={"global": True},
                ))

        except Exception as e:
            errors.append(f"Failed to scan npm: {e}")

        # Check .npmrc for tokens
        npmrc_path = Path.home() / ".npmrc"
        if npmrc_path.exists():
            try:
                content = npmrc_path.read_text()
                if "_authToken" in content or "_password" in content:
                    sensitive.append(Item(
                        name=".npmrc",
                        path=str(npmrc_path),
                        content=content,
                        source="npm",
                        sensitive=True,
                    ))
            except Exception:
                pass

        return ScanResult(source="npm", items=items, sensitive=sensitive, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_npm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/npm.py tests/test_scanner/test_npm.py
git commit -m "feat: npm scanner with .npmrc token detection"
```

---

### Task 7: Environment Variables Scanner

**Files:**
- Create: `src/supersync/scanner/env_vars.py`
- Create: `tests/test_scanner/test_env_vars.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_env_vars.py`:
```python
from supersync.scanner.env_vars import EnvVarsScanner
from supersync.scanner.base import ScanResult


def test_env_vars_scan_extracts_exports(tmp_path):
    scanner = EnvVarsScanner()

    zshrc = tmp_path / ".zshrc"
    zshrc.write_text('export PYTHONPATH="/usr/local/lib/python3"\nexport JAVA_HOME="/Library/Java"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "env_vars"
    assert any(item.name == "PYTHONPATH" for item in result.items)


def test_env_vars_scan_detects_sensitive_vars(tmp_path):
    from unittest.mock import patch
    scanner = EnvVarsScanner()

    zshrc = tmp_path / ".zshrc"
    zshrc.write_text('export GITHUB_TOKEN="ghp_abc123"\nexport PYTHONPATH="/usr/local"\n')

    with patch("supersync.scanner.env_vars.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "GITHUB_TOKEN" and item.sensitive for item in result.sensitive)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_env_vars.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement EnvVarsScanner**

`src/supersync/scanner/env_vars.py`:
```python
import re
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase

# Patterns that indicate sensitive environment variables
SENSITIVE_PATTERNS = re.compile(
    r"(token|secret|key|password|credential|auth|api_key|private)",
    re.IGNORECASE,
)

# Shell config files to scan for exports
SHELL_CONFIGS = [".zshrc", ".bashrc", ".bash_profile"]

# Export pattern: export VAR="value" or export VAR=value
EXPORT_PATTERN = re.compile(r'^export\s+(\w+)=(.+)$', re.MULTILINE)


class EnvVarsScanner(ScannerBase):
    """Scans shell config files for exported environment variables."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        home = Path.home()

        for config_file in SHELL_CONFIGS:
            config_path = home / config_file
            if not config_path.exists():
                continue

            try:
                content = config_path.read_text()
                for match in EXPORT_PATTERN.finditer(content):
                    name = match.group(1)
                    value = match.group(2).strip().strip('"').strip("'")

                    item = Item(
                        name=name,
                        value=value,
                        source="env_vars",
                        sensitive=SENSITIVE_PATTERNS.search(name) is not None,
                        extra={"config_file": config_file},
                    )

                    if item.sensitive:
                        sensitive.append(item)
                    else:
                        items.append(item)

            except Exception as e:
                errors.append(f"Failed to read {config_file}: {e}")

        return ScanResult(source="env_vars", items=items, sensitive=sensitive, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_env_vars.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/env_vars.py tests/test_scanner/test_env_vars.py
git commit -m "feat: environment variables scanner with sensitive detection"
```

---

### Task 8: Dotfiles Scanner

**Files:**
- Create: `src/supersync/scanner/dotfiles.py`
- Create: `tests/test_scanner/test_dotfiles.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_dotfiles.py`:
```python
from unittest.mock import patch
from supersync.scanner.dotfiles import DotfilesScanner
from supersync.scanner.base import ScanResult


def test_dotfiles_scan_reads_existing_files(tmp_path):
    scanner = DotfilesScanner()

    (tmp_path / ".zshrc").write_text("alias ll='ls -la'\n")
    (tmp_path / ".gitconfig").write_text("[user]\n  name = Test\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "dotfiles"
    assert any(item.name == ".zshrc" for item in result.items)
    assert any(item.name == ".gitconfig" for item in result.items)


def test_dotfiles_scan_marks_ssh_as_sensitive(tmp_path):
    scanner = DotfilesScanner()

    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "config").write_text("Host github.com\n")
    (tmp_path / ".zshrc").write_text("alias ll='ls -la'\n")

    with patch("supersync.scanner.dotfiles.Path.home", return_value=tmp_path):
        result = scanner.scan()

    assert any(item.name == "config" and item.sensitive for item in result.sensitive)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_dotfiles.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement DotfilesScanner**

`src/supersync/scanner/dotfiles.py`:
```python
import base64
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase

# Dotfiles to scan (relative to home directory)
DOTFILES_PATHS = [
    ".zshrc",
    ".bashrc",
    ".bash_profile",
    ".gitconfig",
    ".gitignore_global",
    ".vimrc",
    ".editorconfig",
    ".config/starship.toml",
]

# SSH files are always sensitive
SSH_DIR = ".ssh"
SSH_FILES = ["config", "known_hosts"]


class DotfilesScanner(ScannerBase):
    """Scans dotfiles and SSH config files."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        home = Path.home()

        # Scan regular dotfiles
        for rel_path in DOTFILES_PATHS:
            file_path = home / rel_path
            if not file_path.exists():
                continue

            try:
                content = base64.b64encode(file_path.read_bytes()).decode("ascii")
                items.append(Item(
                    name=file_path.name,
                    path=rel_path,
                    content=content,
                    source="dotfiles",
                    sensitive=False,
                ))
            except Exception as e:
                errors.append(f"Failed to read {rel_path}: {e}")

        # Scan SSH files (always sensitive)
        ssh_dir = home / SSH_DIR
        if ssh_dir.exists():
            for ssh_file in SSH_FILES:
                ssh_path = ssh_dir / ssh_file
                if not ssh_path.exists():
                    continue

                try:
                    content = base64.b64encode(ssh_path.read_bytes()).decode("ascii")
                    sensitive.append(Item(
                        name=ssh_file,
                        path=f"{SSH_DIR}/{ssh_file}",
                        content=content,
                        source="dotfiles",
                        sensitive=True,
                    ))
                except Exception as e:
                    errors.append(f"Failed to read {SSH_DIR}/{ssh_file}: {e}")

        return ScanResult(source="dotfiles", items=items, sensitive=sensitive, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_dotfiles.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/dotfiles.py tests/test_scanner/test_dotfiles.py
git commit -m "feat: dotfiles scanner with SSH sensitivity marking"
```

---

### Task 9: IDE Scanner (VS Code)

**Files:**
- Create: `src/supersync/scanner/ide.py`
- Create: `tests/test_scanner/test_ide.py`

- [ ] **Step 1: Write failing test**

`tests/test_scanner/test_ide.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.scanner.ide import IdeScanner
from supersync.scanner.base import ScanResult


def test_ide_scan_parses_vscode_extensions():
    scanner = IdeScanner()

    mock_result = MagicMock()
    mock_result.stdout = "ms-python.python\nesbenp.prettier-vscode\n"

    with patch("supersync.scanner.ide.run_command", return_value=mock_result):
        with patch("supersync.scanner.ide.run_command_optional", return_value=mock_result):
            with patch("pathlib.Path.exists", return_value=False):
                result = scanner.scan()

    assert isinstance(result, ScanResult)
    assert result.source == "ide"
    assert len(result.items) == 2
    assert result.items[0].name == "ms-python.python"


def test_ide_scan_handles_vscode_not_found():
    scanner = IdeScanner()

    with patch("supersync.scanner.ide.run_command_optional", return_value=None):
        result = scanner.scan()

    assert result.source == "ide"
    assert len(result.items) == 0
    assert len(result.errors) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner/test_ide.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement IdeScanner**

`src/supersync/scanner/ide.py`:
```python
import base64
import re
from pathlib import Path

from supersync.scanner.base import Item, ScanResult, ScannerBase
from supersync.utils.run import run_command, run_command_optional

# macOS VS Code settings path
VSCODE_SETTINGS_PATH = "Library/Application Support/Code/User/settings.json"

# Patterns that indicate sensitive settings
SENSITIVE_SETTINGS_PATTERNS = re.compile(
    r"(token|secret|key|password|credential|auth)",
    re.IGNORECASE,
)


class IdeScanner(ScannerBase):
    """Scans IDE configurations (VS Code extensions and settings)."""

    def scan(self) -> ScanResult:
        items: list[Item] = []
        sensitive: list[Item] = []
        errors: list[str] = []

        # Check if VS Code CLI is available
        code_check = run_command_optional("code", "--version")
        if code_check is None:
            return ScanResult(
                source="ide",
                items=[],
                sensitive=[],
                errors=["VS Code CLI not found (code command unavailable)"],
            )

        # Scan VS Code extensions
        try:
            ext_result = run_command("code", "--list-extensions")
            extensions = [line.strip() for line in ext_result.stdout.strip().split("\n") if line.strip()]

            for ext_id in extensions:
                items.append(Item(
                    name=ext_id,
                    source="ide",
                    extra={"ide": "vscode", "type": "extension"},
                ))

        except Exception as e:
            errors.append(f"Failed to scan VS Code extensions: {e}")

        # Scan VS Code settings
        settings_path = Path.home() / VSCODE_SETTINGS_PATH
        if settings_path.exists():
            try:
                content = base64.b64encode(settings_path.read_bytes()).decode("ascii")
                raw_content = settings_path.read_text()

                is_sensitive = bool(SENSITIVE_SETTINGS_PATTERNS.search(raw_content))

                item = Item(
                    name="settings.json",
                    path=VSCODE_SETTINGS_PATH,
                    content=content,
                    source="ide",
                    sensitive=is_sensitive,
                    extra={"ide": "vscode", "type": "settings"},
                )

                if is_sensitive:
                    sensitive.append(item)
                else:
                    items.append(item)

            except Exception as e:
                errors.append(f"Failed to read VS Code settings: {e}")

        return ScanResult(source="ide", items=items, sensitive=sensitive, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner/test_ide.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/scanner/ide.py tests/test_scanner/test_ide.py
git commit -m "feat: VS Code IDE scanner with settings sensitivity detection"
```

---

### Task 10: Manifest Schema (Pydantic Models)

**Files:**
- Create: `src/supersync/manifest/__init__.py`
- Create: `src/supersync/manifest/schema.py`
- Create: `tests/test_manifest/__init__.py`
- Create: `tests/test_manifest/test_schema.py`

- [ ] **Step 1: Write failing test**

`tests/test_manifest/__init__.py`:
```python
```

`tests/test_manifest/test_schema.py`:
```python
from supersync.manifest.schema import (
    BrewPackage,
    PipPackage,
    NpmPackage,
    EnvVar,
    Dotfile,
    VscodeConfig,
    Manifest,
)


def test_brew_package():
    pkg = BrewPackage(name="git", version="2.45.0", package_type="formula")
    assert pkg.name == "git"
    assert pkg.package_type == "formula"


def test_manifest_creation():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={},
        env_vars=[],
        dotfiles=[],
        ide={},
    )
    assert manifest.version == "1.0"
    assert manifest.platform == "macos"


def test_manifest_serialization_roundtrip():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={
            "brew": BrewPackage(name="git", version="2.45.0", package_type="formula"),
        },
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[Dotfile(path=".zshrc", content="abc123", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )
    data = manifest.model_dump()
    restored = Manifest.model_validate(data)
    assert restored.version == manifest.version
    assert len(restored.env_vars) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manifest/test_schema.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement Manifest schema**

`src/supersync/manifest/__init__.py`:
```python
from supersync.manifest.schema import Manifest

__all__ = ["Manifest"]
```

`src/supersync/manifest/schema.py`:
```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BrewPackage(BaseModel):
    name: str
    version: str
    package_type: str = Field(alias="type", default="formula")

    model_config = {"populate_by_name": True}


class PipPackage(BaseModel):
    name: str
    version: str


class NpmPackage(BaseModel):
    name: str
    version: str
    global_: bool = Field(alias="global", default=True)

    model_config = {"populate_by_name": True}


class EnvVar(BaseModel):
    key: str
    value: str


class Dotfile(BaseModel):
    path: str
    content: str  # base64-encoded
    sensitive: bool = False
    encrypted: bool = False


class VscodeConfig(BaseModel):
    extensions: list[str] = Field(default_factory=list)
    settings_path: Optional[str] = None
    settings_content: Optional[str] = None  # base64-encoded


class Manifest(BaseModel):
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    hostname: str = ""
    platform: str = ""
    arch: str = ""
    packages: dict[str, list[BrewPackage | PipPackage | NpmPackage]] = Field(default_factory=dict)
    env_vars: list[EnvVar] = Field(default_factory=list)
    dotfiles: list[Dotfile] = Field(default_factory=list)
    ide: dict[str, VscodeConfig] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manifest/test_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/manifest/ tests/test_manifest/
git commit -m "feat: manifest Pydantic schema with all data models"
```

---

### Task 11: Manifest Serializer (YAML)

**Files:**
- Create: `src/supersync/manifest/serializer.py`
- Create: `tests/test_manifest/test_serializer.py`

- [ ] **Step 1: Write failing test**

`tests/test_manifest/test_serializer.py`:
```python
from supersync.manifest.schema import Manifest, EnvVar
from supersync.manifest.serializer import serialize_manifest, deserialize_manifest


def test_serialize_deserialize_roundtrip():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={},
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[],
        ide={},
    )

    yaml_str = serialize_manifest(manifest)
    assert isinstance(yaml_str, str)
    assert "FOO" in yaml_str

    restored = deserialize_manifest(yaml_str)
    assert restored.version == manifest.version
    assert len(restored.env_vars) == 1
    assert restored.env_vars[0].key == "FOO"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manifest/test_serializer.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement serializer**

`src/supersync/manifest/serializer.py`:
```python
import yaml

from supersync.manifest.schema import Manifest


def serialize_manifest(manifest: Manifest) -> str:
    """Serialize a Manifest to YAML string."""
    data = manifest.model_dump(mode="json")
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def deserialize_manifest(yaml_str: str) -> Manifest:
    """Deserialize a YAML string to a Manifest."""
    data = yaml.safe_load(yaml_str)
    return Manifest.model_validate(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manifest/test_serializer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/manifest/serializer.py tests/test_manifest/test_serializer.py
git commit -m "feat: YAML manifest serializer with roundtrip support"
```

---

### Task 12: Crypto Module (AES-256-GCM)

**Files:**
- Create: `src/supersync/manifest/crypto.py`
- Create: `tests/test_manifest/test_crypto.py`

- [ ] **Step 1: Write failing test**

`tests/test_manifest/test_crypto.py`:
```python
from supersync.manifest.crypto import encrypt_data, decrypt_data


def test_encrypt_decrypt_roundtrip():
    original = b"Hello, SuperSync!"
    password = "test-password-123"

    encrypted = encrypt_data(original, password)
    assert isinstance(encrypted, bytes)
    assert encrypted != original
    assert encrypted[:4] == b"SSNC"  # magic bytes

    decrypted = decrypt_data(encrypted, password)
    assert decrypted == original


def test_decrypt_with_wrong_password_fails():
    original = b"Secret data"
    password = "correct-password"

    encrypted = encrypt_data(original, password)

    import pytest
    with pytest.raises(Exception):
        decrypt_data(encrypted, "wrong-password")


def test_encrypted_file_format():
    original = b"Test data"
    password = "password123"

    encrypted = encrypt_data(original, password)

    # Check magic bytes
    assert encrypted[0:4] == b"SSNC"
    # Check version (2 bytes, big endian)
    version = int.from_bytes(encrypted[4:6], "big")
    assert version == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manifest/test_crypto.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement crypto module**

`src/supersync/manifest/crypto.py`:
```python
import gzip
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"SSNC"
VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KDF_ITERATIONS = 100_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_data(data: bytes, password: str) -> bytes:
    """Encrypt data with AES-256-GCM after gzip compression.

    File format:
    [4 bytes: magic "SSNC"]
    [2 bytes: version (big endian)]
    [16 bytes: salt]
    [12 bytes: nonce]
    [4 bytes: compressed data length (big endian)]
    [N bytes: encrypted compressed data]
    [16 bytes: GCM tag]
    """
    import os

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)

    compressed = gzip.compress(data)
    compressed_len = len(compressed)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, compressed, None)

    # ciphertext includes the GCM tag (last 16 bytes)
    encrypted_payload = ciphertext[:-16]
    gcm_tag = ciphertext[-16:]

    header = (
        MAGIC
        + struct.pack(">H", VERSION)
        + salt
        + nonce
        + struct.pack(">I", compressed_len)
    )

    return header + encrypted_payload + gcm_tag


def decrypt_data(encrypted: bytes, password: str) -> bytes:
    """Decrypt a .supersync file and return the original data."""
    # Parse header
    if encrypted[:4] != MAGIC:
        raise ValueError("Invalid file format: missing SSNC magic bytes")

    version = struct.unpack(">H", encrypted[4:6])[0]
    if version != VERSION:
        raise ValueError(f"Unsupported version: {version}")

    salt = encrypted[6:22]
    nonce = encrypted[22:34]
    compressed_len = struct.unpack(">I", encrypted[34:38])[0]

    encrypted_payload = encrypted[38:38 + compressed_len]
    gcm_tag = encrypted[38 + compressed_len:38 + compressed_len + 16]

    key = _derive_key(password, salt)

    # Reconstruct ciphertext with tag for AESGCM.decrypt
    ciphertext = encrypted_payload + gcm_tag

    aesgcm = AESGCM(key)
    compressed = aesgcm.decrypt(nonce, ciphertext, None)

    return gzip.decompress(compressed)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manifest/test_crypto.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/manifest/crypto.py tests/test_manifest/test_crypto.py
git commit -m "feat: AES-256-GCM encryption module with .supersync file format"
```

---

### Task 13: CLI Scan Command (Full Flow)

**Files:**
- Modify: `src/supersync/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for scan command**

`tests/test_cli.py`:
```python
from typer.testing import CliRunner
from supersync.cli import app

runner = CliRunner()


def test_scan_command_runs():
    result = runner.invoke(app, ["scan", "--skip-sensitive"])
    # Should not crash even if no packages are installed
    assert result.exit_code == 0


def test_version_command():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: May partially pass — need to update cli.py with full implementation

- [ ] **Step 3: Implement full scan command in cli.py**

Replace `src/supersync/cli.py` with:

```python
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from supersync import __version__
from supersync.scanner.base import ScanResult, Item
from supersync.scanner.brew import BrewScanner
from supersync.scanner.pip_scanner import PipScanner
from supersync.scanner.npm import NpmScanner
from supersync.scanner.env_vars import EnvVarsScanner
from supersync.scanner.dotfiles import DotfilesScanner
from supersync.scanner.ide import IdeScanner
from supersync.manifest.schema import (
    Manifest,
    BrewPackage,
    PipPackage,
    NpmPackage,
    EnvVar,
    Dotfile,
    VscodeConfig,
)
from supersync.manifest.serializer import serialize_manifest
from supersync.manifest.crypto import encrypt_data

app = typer.Typer(
    name="supersync",
    help="Cross-device development environment migration tool.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool):
    if value:
        console.print(f"SuperSync v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", help="Show version", callback=_version_callback, is_eager=True,
    ),
):
    """SuperSync - Cross-device development environment migration tool."""


def _run_all_scanners() -> list[ScanResult]:
    """Run all scanners and collect results."""
    scanners = [
        BrewScanner(),
        PipScanner(),
        NpmScanner(),
        EnvVarsScanner(),
        DotfilesScanner(),
        IdeScanner(),
    ]

    results = []
    for scanner in scanners:
        try:
            result = scanner.scan()
            results.append(result)
        except Exception as e:
            results.append(ScanResult(
                source=scanner.__class__.__name__,
                items=[],
                sensitive=[],
                errors=[f"Scanner failed: {e}"],
            ))

    return results


def _collect_sensitive_items(results: list[ScanResult]) -> list[tuple[str, Item]]:
    """Collect all sensitive items from scan results with source info."""
    sensitive = []
    for result in results:
        for item in result.sensitive:
            sensitive.append((result.source, item))
    return sensitive


def _prompt_sensitive_choices(sensitive: list[tuple[str, Item]], skip_all: bool, include_all: bool) -> list[tuple[str, Item, str]]:
    """Prompt user about sensitive items. Returns list of (source, item, action)."""
    if not sensitive:
        return []

    if skip_all:
        return []

    if include_all:
        return [(src, item, "encrypt") for src, item in sensitive]

    console.print(Panel("Sensitive items detected. Choose how to handle each:", title="Sensitive Data"))

    choices = []
    for i, (source, item) in enumerate(sensitive, 1):
        console.print(f"  [{i}] {item.name} ({source}) - {item.path or ''}")
        action = typer.prompt(
            f"    Action for [{i}]",
            type=typer.Choice(["exclude", "include", "encrypt"]),
            default="exclude",
        )
        if action != "exclude":
            choices.append((source, item, action))

    return choices


def _build_manifest(results: list[ScanResult], sensitive_choices: list[tuple[str, Item, str]]) -> Manifest:
    """Build a Manifest from scan results and sensitive item choices."""
    import platform

    brew_packages = []
    pip_packages = []
    npm_packages = []
    env_vars = []
    dotfiles = []
    vscode_extensions = []
    vscode_settings_path = None
    vscode_settings_content = None

    for result in results:
        if result.source == "brew":
            for item in result.items:
                pkg_type = item.extra.get("type", "formula")
                brew_packages.append(BrewPackage(name=item.name, version=item.version or "unknown", package_type=pkg_type))

        elif result.source == "pip":
            for item in result.items:
                pip_packages.append(PipPackage(name=item.name, version=item.version or "unknown"))

        elif result.source == "npm":
            for item in result.items:
                npm_packages.append(NpmPackage(name=item.name, version=item.version or "unknown"))

        elif result.source == "env_vars":
            for item in result.items:
                env_vars.append(EnvVar(key=item.name, value=item.value or ""))

        elif result.source == "dotfiles":
            for item in result.items:
                dotfiles.append(Dotfile(path=item.path or item.name, content=item.content or "", sensitive=False))

        elif result.source == "ide":
            for item in result.items:
                if item.extra.get("type") == "extension":
                    vscode_extensions.append(item.name)
                elif item.extra.get("type") == "settings":
                    vscode_settings_path = item.path
                    vscode_settings_content = item.content

    # Add sensitive items chosen by user
    for source, item, action in sensitive_choices:
        if source == "env_vars":
            env_vars.append(EnvVar(key=item.name, value=item.value or ""))
        elif source == "dotfiles":
            dotfiles.append(Dotfile(
                path=item.path or item.name,
                content=item.content or "",
                sensitive=True,
                encrypted=(action == "encrypt"),
            ))
        elif source == "npm":
            dotfiles.append(Dotfile(
                path=item.path or ".npmrc",
                content=item.content or "",
                sensitive=True,
                encrypted=(action == "encrypt"),
            ))
        elif source == "ide":
            vscode_settings_path = item.path
            vscode_settings_content = item.content

    packages = {}
    if brew_packages:
        packages["brew"] = brew_packages
    if pip_packages:
        packages["pip"] = pip_packages
    if npm_packages:
        packages["npm"] = npm_packages

    ide = {}
    if vscode_extensions or vscode_settings_content:
        ide["vscode"] = VscodeConfig(
            extensions=vscode_extensions,
            settings_path=vscode_settings_path,
            settings_content=vscode_settings_content,
        )

    return Manifest(
        version="1.0",
        hostname=platform.node(),
        platform="macos",
        arch=platform.machine(),
        packages=packages,
        env_vars=env_vars,
        dotfiles=dotfiles,
        ide=ide,
    )


@app.command()
def scan(
    output: str = typer.Option("env.supersync", "--output", "-o", help="Output file path"),
    skip_sensitive: bool = typer.Option(False, "--skip-sensitive", help="Skip all sensitive items"),
    include_all_sensitive: bool = typer.Option(False, "--include-all-sensitive", help="Include all sensitive items (encrypted)"),
) -> None:
    """Scan current development environment and generate encrypted snapshot."""
    console.print("[bold blue]SuperSync[/bold blue] - Scanning environment...\n")

    # Run all scanners
    results = _run_all_scanners()

    # Display scan summary
    table = Table(title="Scan Results")
    table.add_column("Source", style="cyan")
    table.add_column("Items", justify="right", style="green")
    table.add_column("Sensitive", justify="right", style="yellow")
    table.add_column("Errors", justify="right", style="red")

    for result in results:
        table.add_row(
            result.source,
            str(len(result.items)),
            str(len(result.sensitive)),
            str(len(result.errors)),
        )

    console.print(table)

    # Print any errors
    for result in results:
        for error in result.errors:
            console.print(f"[yellow]Warning ({result.source}):[/yellow] {error}")

    # Handle sensitive items
    sensitive = _collect_sensitive_items(results)
    sensitive_choices = _prompt_sensitive_choices(sensitive, skip_sensitive, include_all_sensitive)

    # Build manifest
    manifest = _build_manifest(results, sensitive_choices)

    # Serialize and encrypt
    yaml_data = serialize_manifest(manifest)

    # Prompt for password
    password = typer.prompt("Enter encryption password", hide_input=True)
    password_confirm = typer.prompt("Confirm password", hide_input=True)
    if password != password_confirm:
        console.print("[red]Passwords do not match![/red]")
        raise typer.Exit(code=1)

    if len(password) < 8:
        console.print("[red]Password must be at least 8 characters![/red]")
        raise typer.Exit(code=1)

    encrypted = encrypt_data(yaml_data.encode("utf-8"), password)

    # Write output file
    output_path = Path(output)
    output_path.write_bytes(encrypted)

    console.print(f"\n[bold green]Environment snapshot saved to {output_path}[/bold green]")
    console.print(f"File size: {len(encrypted):,} bytes")


@app.command()
def restore(
    file: str = typer.Argument(..., help="Path to .supersync file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, do not execute"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm all prompts"),
) -> None:
    """Restore development environment from a .supersync file."""
    from supersync.manifest.crypto import decrypt_data
    from supersync.manifest.serializer import deserialize_manifest
    from supersync.provisioner.engine import ProvisionerEngine

    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    # Decrypt
    password = typer.prompt("Enter decryption password", hide_input=True)

    try:
        encrypted_data = file_path.read_bytes()
        yaml_data = decrypt_data(encrypted_data, password)
        manifest = deserialize_manifest(yaml_data.decode("utf-8"))
    except Exception as e:
        console.print(f"[red]Decryption failed: {e}[/red]")
        raise typer.Exit(code=1)

    # Display manifest summary
    console.print(Panel(f"Environment from [cyan]{manifest.hostname}[/cyan] ({manifest.platform}/{manifest.arch})", title="Manifest"))

    # Run provisioner
    engine = ProvisionerEngine(manifest, dry_run=dry_run, auto_confirm=yes)
    report = engine.run()

    # Display report
    console.print(report.format())


@app.command()
def inspect(
    file: str = typer.Argument(..., help="Path to .supersync file"),
) -> None:
    """Decrypt and display the contents of a .supersync file."""
    from supersync.manifest.crypto import decrypt_data
    from supersync.manifest.serializer import deserialize_manifest

    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    password = typer.prompt("Enter decryption password", hide_input=True)

    try:
        encrypted_data = file_path.read_bytes()
        yaml_data = decrypt_data(encrypted_data, password)
        manifest = deserialize_manifest(yaml_data.decode("utf-8"))
    except Exception as e:
        console.print(f"[red]Decryption failed: {e}[/red]")
        raise typer.Exit(code=1)

    # Display manifest
    console.print(Panel(f"Environment from [cyan]{manifest.hostname}[/cyan]", title="Manifest Info"))
    console.print(f"  Platform: {manifest.platform}/{manifest.arch}")
    console.print(f"  Created: {manifest.created_at}")

    if "brew" in manifest.packages:
        console.print(f"\n  Brew packages: {len([p for p in manifest.packages['brew'] if p.package_type == 'formula'])} formulae, {len([p for p in manifest.packages['brew'] if p.package_type == 'cask'])} casks")

    if "pip" in manifest.packages:
        console.print(f"  Pip packages: {len(manifest.packages['pip'])}")

    if "npm" in manifest.packages:
        console.print(f"  Npm packages: {len(manifest.packages['npm'])}")

    console.print(f"  Environment variables: {len(manifest.env_vars)}")
    console.print(f"  Dotfiles: {len(manifest.dotfiles)}")

    if "vscode" in manifest.ide:
        console.print(f"  VS Code extensions: {len(manifest.ide['vscode'].extensions)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/cli.py tests/test_cli.py
git commit -m "feat: full CLI scan command with scanner orchestration and encryption"
```

---

### Task 14: Dependency Topological Sort

**Files:**
- Create: `src/supersync/provisioner/__init__.py`
- Create: `src/supersync/provisioner/dependency.py`
- Create: `tests/test_provisioner/__init__.py`
- Create: `tests/test_provisioner/test_dependency.py`

- [ ] **Step 1: Write failing test**

`tests/test_provisioner/__init__.py`:
```python
```

`tests/test_provisioner/test_dependency.py`:
```python
from supersync.provisioner.dependency import topological_sort, Step, StepType


def test_topological_sort_order():
    steps = [
        Step(type=StepType.IDE_EXTENSION, name="python", source="ide"),
        Step(type=StepType.BREW_FORMULA, name="git", source="brew"),
        Step(type=StepType.ENV_VAR, name="FOO", source="env_vars"),
        Step(type=StepType.DOTFILE, name=".zshrc", source="dotfiles"),
        Step(type=StepType.PIP_PACKAGE, name="requests", source="pip"),
        Step(type=StepType.NPM_PACKAGE, name="typescript", source="npm"),
    ]

    sorted_steps = topological_sort(steps)

    # Brew should come before pip and npm
    brew_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.BREW_FORMULA)
    pip_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.PIP_PACKAGE)
    npm_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.NPM_PACKAGE)

    assert brew_idx < pip_idx
    assert brew_idx < npm_idx

    # Env vars before dotfiles
    env_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.ENV_VAR)
    dotfile_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.DOTFILE)

    assert env_idx < dotfile_idx

    # IDE extensions last
    ide_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.IDE_EXTENSION)
    assert ide_idx > pip_idx
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provisioner/test_dependency.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement dependency sort**

`src/supersync/provisioner/__init__.py`:
```python
```

`src/supersync/provisioner/dependency.py`:
```python
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class StepType(IntEnum):
    """Execution order for provisioner steps (lower = earlier)."""
    BREW_FORMULA = 10
    BREW_CASK = 11
    PIP_PACKAGE = 20
    NPM_PACKAGE = 21
    ENV_VAR = 30
    DOTFILE = 40
    IDE_EXTENSION = 50


@dataclass
class Step:
    """A single provisioner step."""
    type: StepType
    name: str
    source: str
    version: Optional[str] = None
    content: Optional[str] = None
    path: Optional[str] = None
    sensitive: bool = False
    encrypted: bool = False
    extra: dict = field(default_factory=dict)


def topological_sort(steps: list[Step]) -> list[Step]:
    """Sort steps by dependency order.

    Order: brew → pip/npm → env_vars → dotfiles → IDE
    """
    return sorted(steps, key=lambda s: s.type.value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_provisioner/test_dependency.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/provisioner/ tests/test_provisioner/
git commit -m "feat: dependency topological sort for provisioner steps"
```

---

### Task 15: Package Installer

**Files:**
- Create: `src/supersync/provisioner/installer.py`
- Create: `tests/test_provisioner/test_installer.py`

- [ ] **Step 1: Write failing test**

`tests/test_provisioner/test_installer.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.provisioner.installer import Installer, InstallResult, InstallStatus


def test_install_brew_formula():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_brew_formula("git", "2.45.0")

    assert result.status == InstallStatus.SUCCESS


def test_install_brew_formula_already_installed():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        # brew install returns 1 with "already installed" message
        mock_run.return_value = MagicMock(returncode=1, stderr="already installed")
        result = installer.install_brew_formula("git", "2.45.0")

    assert result.status == InstallStatus.SKIPPED


def test_install_pip_package():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_pip_package("requests", "2.32.0")

    assert result.status == InstallStatus.SUCCESS


def test_install_vscode_extension():
    installer = Installer()

    with patch("supersync.provisioner.installer.run_command") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = installer.install_vscode_extension("ms-python.python")

    assert result.status == InstallStatus.SUCCESS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provisioner/test_installer.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement Installer**

`src/supersync/provisioner/installer.py`:
```python
from dataclasses import dataclass
from enum import Enum

from supersync.utils.run import run_command, run_command_optional


class InstallStatus(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class InstallResult:
    name: str
    status: InstallStatus
    message: str = ""


class Installer:
    """Handles package installation for various package managers."""

    def install_brew_formula(self, name: str, version: str) -> InstallResult:
        result = run_command("brew", "install", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stderr or "already installed" in result.stdout:
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_brew_cask(self, name: str, version: str) -> InstallResult:
        result = run_command("brew", "install", "--cask", name, check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stderr or "already installed" in result.stdout:
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_pip_package(self, name: str, version: str) -> InstallResult:
        result = run_command("pip", "install", f"{name}=={version}", check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        elif "already satisfied" in result.stdout.lower():
            return InstallResult(name=name, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_npm_package(self, name: str, version: str) -> InstallResult:
        result = run_command("npm", "install", "-g", f"{name}@{version}", check=False)
        if result.returncode == 0:
            return InstallResult(name=name, status=InstallStatus.SUCCESS)
        else:
            return InstallResult(name=name, status=InstallStatus.FAILED, message=result.stderr.strip())

    def install_vscode_extension(self, extension_id: str) -> InstallResult:
        result = run_command("code", "--install-extension", extension_id, check=False)
        if result.returncode == 0:
            return InstallResult(name=extension_id, status=InstallStatus.SUCCESS)
        elif "already installed" in result.stdout.lower():
            return InstallResult(name=extension_id, status=InstallStatus.SKIPPED, message="Already installed")
        else:
            return InstallResult(name=extension_id, status=InstallStatus.FAILED, message=result.stderr.strip())

    def inject_env_var(self, key: str, value: str, shell_config: str = "~/.zshrc") -> InstallResult:
        """Append an export statement to the shell config file."""
        from pathlib import Path

        config_path = Path(shell_config).expanduser()
        export_line = f'export {key}="{value}"\n'

        try:
            if config_path.exists():
                content = config_path.read_text()
                if f"export {key}=" in content:
                    return InstallResult(name=key, status=InstallStatus.SKIPPED, message="Already defined")

            with open(config_path, "a") as f:
                f.write(export_line)

            return InstallResult(name=key, status=InstallStatus.SUCCESS)

        except Exception as e:
            return InstallResult(name=key, status=InstallStatus.FAILED, message=str(e))

    def deploy_dotfile(self, rel_path: str, content_b64: str, backup: bool = True) -> InstallResult:
        """Deploy a dotfile from base64-encoded content."""
        import base64
        from pathlib import Path

        target = Path.home() / rel_path

        try:
            if target.exists() and backup:
                backup_path = Path(str(target) + ".supersync.bak")
                backup_path.write_bytes(target.read_bytes())

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(content_b64))

            return InstallResult(name=rel_path, status=InstallStatus.SUCCESS)

        except Exception as e:
            return InstallResult(name=rel_path, status=InstallStatus.FAILED, message=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_provisioner/test_installer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/provisioner/installer.py tests/test_provisioner/test_installer.py
git commit -m "feat: package installer for brew, pip, npm, vscode, env vars, dotfiles"
```

---

### Task 16: Conflict Handler

**Files:**
- Create: `src/supersync/provisioner/conflict.py`
- Create: `tests/test_provisioner/test_conflict.py`

- [ ] **Step 1: Write failing test**

`tests/test_provisioner/test_conflict.py`:
```python
from supersync.provisioner.conflict import ConflictDetector, Conflict, ConflictType


def test_detect_dotfile_conflict(tmp_path):
    detector = ConflictDetector()

    # Create existing dotfile
    (tmp_path / ".zshrc").write_text("existing content")

    conflicts = detector.detect_dotfile_conflicts(
        dotfiles=[{"path": ".zshrc", "content": "new content"}],
        home_dir=tmp_path,
    )

    assert len(conflicts) == 1
    assert conflicts[0].type == ConflictType.DOTFILE_EXISTS


def test_detect_no_conflict(tmp_path):
    detector = ConflictDetector()

    conflicts = detector.detect_dotfile_conflicts(
        dotfiles=[{"path": ".zshrc", "content": "new content"}],
        home_dir=tmp_path,
    )

    assert len(conflicts) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provisioner/test_conflict.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement ConflictDetector**

`src/supersync/provisioner/conflict.py`:
```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ConflictType(Enum):
    DOTFILE_EXISTS = "dotfile_exists"
    PACKAGE_VERSION_MISMATCH = "package_version_mismatch"


@dataclass
class Conflict:
    type: ConflictType
    name: str
    message: str
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ConflictDetector:
    """Detects potential conflicts before restoration."""

    def detect_dotfile_conflicts(
        self, dotfiles: list[dict[str, Any]], home_dir: Path
    ) -> list[Conflict]:
        """Check if any dotfiles already exist on the target system."""
        conflicts = []

        for dotfile in dotfiles:
            rel_path = dotfile.get("path", "")
            target_path = home_dir / rel_path

            if target_path.exists():
                conflicts.append(Conflict(
                    type=ConflictType.DOTFILE_EXISTS,
                    name=rel_path,
                    message=f"File already exists: {rel_path}",
                    details={"path": str(target_path)},
                ))

        return conflicts

    def detect_package_conflicts(
        self, packages: dict[str, list], installed_packages: dict[str, dict[str, str]]
    ) -> list[Conflict]:
        """Check for version mismatches in installed packages."""
        conflicts = []

        for manager, pkg_list in packages.items():
            installed = installed_packages.get(manager, {})
            for pkg in pkg_list:
                name = pkg.name if hasattr(pkg, "name") else pkg.get("name", "")
                version = pkg.version if hasattr(pkg, "version") else pkg.get("version", "")

                if name in installed and installed[name] != version:
                    conflicts.append(Conflict(
                        type=ConflictType.PACKAGE_VERSION_MISMATCH,
                        name=name,
                        message=f"Version mismatch for {name}: installed {installed[name]}, manifest {version}",
                        details={
                            "installed_version": installed[name],
                            "manifest_version": version,
                        },
                    ))

        return conflicts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_provisioner/test_conflict.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/provisioner/conflict.py tests/test_provisioner/test_conflict.py
git commit -m "feat: conflict detector for dotfiles and package versions"
```

---

### Task 17: Provisioner Engine

**Files:**
- Create: `src/supersync/provisioner/engine.py`
- Create: `tests/test_provisioner/test_engine.py`

- [ ] **Step 1: Write failing test**

`tests/test_provisioner/test_engine.py`:
```python
from unittest.mock import patch, MagicMock
from supersync.manifest.schema import Manifest, BrewPackage, EnvVar, Dotfile, VscodeConfig
from supersync.provisioner.engine import ProvisionerEngine, RestoreReport, CategoryReport


def test_engine_generates_steps_from_manifest():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test",
        packages={
            "brew": [BrewPackage(name="git", version="2.45.0", package_type="formula")],
        },
        env_vars=[EnvVar(key="FOO", value="bar")],
        dotfiles=[Dotfile(path=".zshrc", content="abc", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )

    engine = ProvisionerEngine(manifest, dry_run=True)
    steps = engine._generate_steps()

    assert len(steps) > 0
    # Brew should be first
    assert steps[0].type.value < steps[-1].type.value


def test_engine_dry_run_does_not_install():
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test",
        packages={
            "brew": [BrewPackage(name="git", version="2.45.0", package_type="formula")],
        },
        env_vars=[],
        dotfiles=[],
        ide={},
    )

    engine = ProvisionerEngine(manifest, dry_run=True)

    with patch("supersync.provisioner.installer.Installer.install_brew_formula") as mock_install:
        report = engine.run()
        mock_install.assert_not_called()

    assert isinstance(report, RestoreReport)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_provisioner/test_engine.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement ProvisionerEngine**

`src/supersync/provisioner/engine.py`:
```python
from dataclasses import dataclass, field
from typing import Optional

from supersync.manifest.schema import Manifest
from supersync.provisioner.dependency import Step, StepType, topological_sort
from supersync.provisioner.installer import Installer, InstallResult, InstallStatus


@dataclass
class CategoryReport:
    category: str
    total: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)

    def add(self, result: InstallResult) -> None:
        self.total += 1
        if result.status == InstallStatus.SUCCESS:
            self.success += 1
        elif result.status == InstallStatus.SKIPPED:
            self.skipped += 1
        elif result.status == InstallStatus.FAILED:
            self.failed += 1
            self.warnings.append(f"{result.name}: {result.message}")


@dataclass
class RestoreReport:
    categories: list[CategoryReport] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(c.total for c in self.categories)

    @property
    def total_success(self) -> int:
        return sum(c.success for c in self.categories)

    @property
    def total_warnings(self) -> int:
        return sum(c.failed for c in self.categories)

    def format(self) -> str:
        lines = []
        for cat in self.categories:
            status = "✅" if cat.failed == 0 else "⚠️"
            detail = f"{cat.success}/{cat.total} successful"
            if cat.skipped:
                detail += f" ({cat.skipped} skipped)"
            lines.append(f"{status} {cat.category}: {detail}")
            for w in cat.warnings:
                lines.append(f"   ⚠️ {w}")

        lines.append("")
        lines.append(f"Total: {self.total_success}/{self.total} successful, {self.total_warnings} warnings")
        return "\n".join(lines)


class ProvisionerEngine:
    """Orchestrates the restoration of a development environment."""

    def __init__(
        self,
        manifest: Manifest,
        dry_run: bool = False,
        auto_confirm: bool = False,
    ) -> None:
        self.manifest = manifest
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        self.installer = Installer()

    def _generate_steps(self) -> list[Step]:
        """Convert manifest into ordered provisioner steps."""
        steps = []

        # Brew packages
        for pkg in self.manifest.packages.get("brew", []):
            step_type = StepType.BREW_CASK if pkg.package_type == "cask" else StepType.BREW_FORMULA
            steps.append(Step(
                type=step_type,
                name=pkg.name,
                version=pkg.version,
                source="brew",
            ))

        # Pip packages
        for pkg in self.manifest.packages.get("pip", []):
            steps.append(Step(
                type=StepType.PIP_PACKAGE,
                name=pkg.name,
                version=pkg.version,
                source="pip",
            ))

        # Npm packages
        for pkg in self.manifest.packages.get("npm", []):
            steps.append(Step(
                type=StepType.NPM_PACKAGE,
                name=pkg.name,
                version=pkg.version,
                source="npm",
            ))

        # Environment variables
        for env in self.manifest.env_vars:
            steps.append(Step(
                type=StepType.ENV_VAR,
                name=env.key,
                content=env.value,
                source="env_vars",
            ))

        # Dotfiles
        for dotfile in self.manifest.dotfiles:
            steps.append(Step(
                type=StepType.DOTFILE,
                name=dotfile.path,
                content=dotfile.content,
                source="dotfiles",
                sensitive=dotfile.sensitive,
                encrypted=dotfile.encrypted,
            ))

        # IDE extensions
        for ide_name, ide_config in self.manifest.ide.items():
            for ext in ide_config.extensions:
                steps.append(Step(
                    type=StepType.IDE_EXTENSION,
                    name=ext,
                    source=ide_name,
                ))

        return topological_sort(steps)

    def run(self) -> RestoreReport:
        """Execute the restoration plan."""
        steps = self._generate_steps()
        report = RestoreReport()

        # Group steps by category for reporting
        current_category = ""
        category_report: Optional[CategoryReport] = None

        for step in steps:
            category_name = self._step_category(step)

            if category_name != current_category:
                if category_report is not None:
                    report.categories.append(category_report)
                category_report = CategoryReport(category=category_name)
                current_category = category_name

            if self.dry_run:
                # In dry-run mode, just count without executing
                category_report.total += 1
                category_report.success += 1
                continue

            result = self._execute_step(step)
            category_report.add(result)

        if category_report is not None:
            report.categories.append(category_report)

        return report

    def _step_category(self, step: Step) -> str:
        """Map step type to category name for reporting."""
        mapping = {
            StepType.BREW_FORMULA: "brew",
            StepType.BREW_CASK: "brew",
            StepType.PIP_PACKAGE: "pip",
            StepType.NPM_PACKAGE: "npm",
            StepType.ENV_VAR: "env_vars",
            StepType.DOTFILE: "dotfiles",
            StepType.IDE_EXTENSION: "vscode",
        }
        return mapping.get(step.type, step.source)

    def _execute_step(self, step: Step) -> InstallResult:
        """Execute a single provisioner step."""
        if step.type == StepType.BREW_FORMULA:
            return self.installer.install_brew_formula(step.name, step.version or "")
        elif step.type == StepType.BREW_CASK:
            return self.installer.install_brew_cask(step.name, step.version or "")
        elif step.type == StepType.PIP_PACKAGE:
            return self.installer.install_pip_package(step.name, step.version or "")
        elif step.type == StepType.NPM_PACKAGE:
            return self.installer.install_npm_package(step.name, step.version or "")
        elif step.type == StepType.ENV_VAR:
            return self.installer.inject_env_var(step.name, step.content or "")
        elif step.type == StepType.DOTFILE:
            return self.installer.deploy_dotfile(step.name, step.content or "")
        elif step.type == StepType.IDE_EXTENSION:
            return self.installer.install_vscode_extension(step.name)
        else:
            return InstallResult(name=step.name, status=InstallStatus.FAILED, message="Unknown step type")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_provisioner/test_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/supersync/provisioner/engine.py tests/test_provisioner/test_engine.py
git commit -m "feat: provisioner engine with step orchestration and restore reports"
```

---

### Task 18: Integration Test (Full Roundtrip)

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

`tests/test_integration.py`:
```python
"""Integration test: scan → encrypt → decrypt → restore (dry-run) roundtrip."""
from unittest.mock import patch, MagicMock

from supersync.manifest.schema import (
    Manifest,
    BrewPackage,
    PipPackage,
    NpmPackage,
    EnvVar,
    Dotfile,
    VscodeConfig,
)
from supersync.manifest.serializer import serialize_manifest, deserialize_manifest
from supersync.manifest.crypto import encrypt_data, decrypt_data
from supersync.provisioner.engine import ProvisionerEngine


def test_full_roundtrip():
    """Test the complete scan → serialize → encrypt → decrypt → restore flow."""

    # 1. Create a manifest (simulating scan output)
    manifest = Manifest(
        version="1.0",
        platform="macos",
        arch="arm64",
        hostname="test-mac",
        packages={
            "brew": [
                BrewPackage(name="git", version="2.45.0", package_type="formula"),
                BrewPackage(name="visual-studio-code", version="1.90.0", package_type="cask"),
            ],
            "pip": [PipPackage(name="requests", version="2.32.0")],
            "npm": [NpmPackage(name="typescript", version="5.5.0")],
        },
        env_vars=[EnvVar(key="PYTHONPATH", value="/usr/local/lib/python3")],
        dotfiles=[Dotfile(path=".zshrc", content="YWxpYXMgbGw9J2xzIC1sYScK", sensitive=False)],
        ide={"vscode": VscodeConfig(extensions=["ms-python.python"])},
    )

    # 2. Serialize to YAML
    yaml_str = serialize_manifest(manifest)
    assert isinstance(yaml_str, str)
    assert "git" in yaml_str

    # 3. Encrypt
    password = "test-integration-password"
    encrypted = encrypt_data(yaml_str.encode("utf-8"), password)
    assert encrypted[:4] == b"SSNC"

    # 4. Decrypt
    decrypted_data = decrypt_data(encrypted, password)
    decrypted_yaml = decrypted_data.decode("utf-8")

    # 5. Deserialize
    restored_manifest = deserialize_manifest(decrypted_yaml)
    assert restored_manifest.version == "1.0"
    assert len(restored_manifest.packages["brew"]) == 2
    assert len(restored_manifest.packages["pip"]) == 1
    assert len(restored_manifest.env_vars) == 1
    assert len(restored_manifest.dotfiles) == 1
    assert len(restored_manifest.ide["vscode"].extensions) == 1

    # 6. Restore (dry-run)
    engine = ProvisionerEngine(restored_manifest, dry_run=True)
    report = engine.run()

    assert report.total > 0
    assert report.total_success > 0


def test_encrypt_decrypt_with_wrong_password():
    """Verify that wrong password raises an error."""
    data = b"test data"
    password = "correct"

    encrypted = encrypt_data(data, password)

    import pytest
    with pytest.raises(Exception):
        decrypt_data(encrypted, "wrong")
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration test for full scan-encrypt-decrypt-restore roundtrip"
```

---

### Task 19: Run All Tests and Final Verification

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Verify CLI works end-to-end**

Run: `supersync --version`
Expected: `SuperSync v0.1.0`

Run: `supersync --help`
Expected: Help text with scan, restore, inspect commands

- [ ] **Step 3: Final commit with any fixes**

If any issues found, fix and commit. Otherwise skip.

- [ ] **Step 4: Push to remote**

```bash
git remote add origin https://github.com/NoWint/SuperSync.git
git push -u origin main
```
