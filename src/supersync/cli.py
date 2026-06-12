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
from supersync.utils.logger import get_logger

app = typer.Typer(
    name="supersync",
    help="Cross-device development environment migration tool.",
    no_args_is_help=True,
)
console = Console()
logger = get_logger()


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
    sensitive = []
    for result in results:
        for item in result.sensitive:
            sensitive.append((result.source, item))
    return sensitive


def _prompt_sensitive_choices(sensitive: list[tuple[str, Item]], skip_all: bool, include_all: bool) -> list[tuple[str, Item, str]]:
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
                env_vars.append(EnvVar(key=item.name, value=item.content or "", config_file=item.extra.get("config_file", ".zshrc")))

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

    for source, item, action in sensitive_choices:
        if source == "env_vars":
            env_vars.append(EnvVar(key=item.name, value=item.content or ""))
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

    results = _run_all_scanners()

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

    for result in results:
        for error in result.errors:
            console.print(f"[yellow]Warning ({result.source}):[/yellow] {error}")

    sensitive = _collect_sensitive_items(results)
    sensitive_choices = _prompt_sensitive_choices(sensitive, skip_sensitive, include_all_sensitive)

    manifest = _build_manifest(results, sensitive_choices)

    yaml_data = serialize_manifest(manifest)

    password = typer.prompt("Enter encryption password", hide_input=True)
    password_confirm = typer.prompt("Confirm password", hide_input=True)
    if password != password_confirm:
        console.print("[red]Passwords do not match![/red]")
        raise typer.Exit(code=1)

    if len(password) < 8:
        console.print("[red]Password must be at least 8 characters![/red]")
        raise typer.Exit(code=1)

    encrypted = encrypt_data(yaml_data.encode("utf-8"), password)

    output_path = Path(output)
    output_path.write_bytes(encrypted)

    console.print(f"\n[bold green]Environment snapshot saved to {output_path}[/bold green]")
    console.print(f"File size: {len(encrypted):,} bytes")
    logger.info("Scan completed: %d items, saved to %s", sum(len(r.items) for r in results), output_path)


@app.command()
def restore(
    file: str = typer.Argument(..., help="Path to .supersync file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, do not execute"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm all prompts"),
    only: Optional[str] = typer.Option(None, "--only", help="Only restore specific categories (comma-separated: brew,pip,npm,env_vars,dotfiles,vscode)"),
) -> None:
    """Restore development environment from a .supersync file."""
    from supersync.manifest.crypto import decrypt_data
    from supersync.manifest.serializer import deserialize_manifest
    from supersync.provisioner.engine import ProvisionerEngine

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

    if only:
        categories = [c.strip() for c in only.split(",")]
        if "brew" not in categories:
            manifest.packages.pop("brew", None)
        if "pip" not in categories:
            manifest.packages.pop("pip", None)
        if "npm" not in categories:
            manifest.packages.pop("npm", None)
        if "env_vars" not in categories:
            manifest.env_vars = []
        if "dotfiles" not in categories:
            manifest.dotfiles = []
        if "vscode" not in categories:
            manifest.ide.pop("vscode", None)

    console.print(Panel(f"Environment from [cyan]{manifest.hostname}[/cyan] ({manifest.platform}/{manifest.arch})", title="Manifest"))

    engine = ProvisionerEngine(manifest, dry_run=dry_run, auto_confirm=yes)
    report = engine.run()

    console.print(report.format())
    logger.info("Restore completed from %s", file_path)


@app.command()
def diff(
    file: str = typer.Argument(..., help="Path to .supersync file to compare against"),
) -> None:
    """Compare current environment with a .supersync snapshot."""
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

    # Scan current environment
    console.print("[bold blue]Scanning current environment for comparison...[/bold blue]\n")
    results = _run_all_scanners()
    current_manifest = _build_manifest(results, [])

    # Compare packages
    table = Table(title="Environment Diff")
    table.add_column("Category", style="cyan")
    table.add_column("In Snapshot Only", style="yellow")
    table.add_column("In Local Only", style="green")
    table.add_column("Common", style="dim")

    # Brew
    snap_brew = {p.name for p in manifest.packages.get("brew", [])}
    curr_brew = {p.name for p in current_manifest.packages.get("brew", [])}
    table.add_row(
        "brew",
        str(len(snap_brew - curr_brew)),
        str(len(curr_brew - snap_brew)),
        str(len(snap_brew & curr_brew)),
    )

    # pip
    snap_pip = {p.name for p in manifest.packages.get("pip", [])}
    curr_pip = {p.name for p in current_manifest.packages.get("pip", [])}
    table.add_row(
        "pip",
        str(len(snap_pip - curr_pip)),
        str(len(curr_pip - snap_pip)),
        str(len(snap_pip & curr_pip)),
    )

    # npm
    snap_npm = {p.name for p in manifest.packages.get("npm", [])}
    curr_npm = {p.name for p in current_manifest.packages.get("npm", [])}
    table.add_row(
        "npm",
        str(len(snap_npm - curr_npm)),
        str(len(curr_npm - snap_npm)),
        str(len(snap_npm & curr_npm)),
    )

    # env_vars
    snap_env = {e.key for e in manifest.env_vars}
    curr_env = {e.key for e in current_manifest.env_vars}
    table.add_row(
        "env_vars",
        str(len(snap_env - curr_env)),
        str(len(curr_env - snap_env)),
        str(len(snap_env & curr_env)),
    )

    # dotfiles
    snap_dot = {d.path for d in manifest.dotfiles}
    curr_dot = {d.path for d in current_manifest.dotfiles}
    table.add_row(
        "dotfiles",
        str(len(snap_dot - curr_dot)),
        str(len(curr_dot - snap_dot)),
        str(len(snap_dot & curr_dot)),
    )

    # vscode
    snap_ext = set()
    curr_ext = set()
    if "vscode" in manifest.ide:
        snap_ext = set(manifest.ide["vscode"].extensions)
    if "vscode" in current_manifest.ide:
        curr_ext = set(current_manifest.ide["vscode"].extensions)
    table.add_row(
        "vscode",
        str(len(snap_ext - curr_ext)),
        str(len(curr_ext - snap_ext)),
        str(len(snap_ext & curr_ext)),
    )

    console.print(table)

    # Show details of missing packages (in snapshot but not local)
    missing_brew = sorted(snap_brew - curr_brew)
    if missing_brew:
        console.print("\n[yellow]Missing brew packages (in snapshot but not installed locally):[/yellow]")
        for pkg in missing_brew[:20]:
            console.print(f"  - {pkg}")
        if len(missing_brew) > 20:
            console.print(f"  ... and {len(missing_brew) - 20} more")

    missing_pip = sorted(snap_pip - curr_pip)
    if missing_pip:
        console.print("\n[yellow]Missing pip packages:[/yellow]")
        for pkg in missing_pip[:20]:
            console.print(f"  - {pkg}")
        if len(missing_pip) > 20:
            console.print(f"  ... and {len(missing_pip) - 20} more")

    missing_ext = sorted(snap_ext - curr_ext)
    if missing_ext:
        console.print("\n[yellow]Missing VS Code extensions:[/yellow]")
        for ext in missing_ext[:20]:
            console.print(f"  - {ext}")
        if len(missing_ext) > 20:
            console.print(f"  ... and {len(missing_ext) - 20} more")

    logger.info("Diff completed against %s", file_path)


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


@app.command(name="list")
def list_items(
    file: str = typer.Argument(..., help="Path to .supersync file"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category: brew, pip, npm, env_vars, dotfiles, vscode"),
) -> None:
    """List detailed contents of a .supersync snapshot."""
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

    console.print(Panel(
        f"Source: [cyan]{manifest.hostname}[/cyan]\n"
        f"Platform: {manifest.platform}/{manifest.arch}\n"
        f"Created: {manifest.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        title="Snapshot Info",
    ))

    if category and category not in ("brew", "pip", "npm", "env_vars", "dotfiles", "vscode"):
        console.print(f"[red]Unknown category: {category}. Valid: brew, pip, npm, env_vars, dotfiles, vscode[/red]")
        raise typer.Exit(code=1)

    if (not category or category == "brew") and "brew" in manifest.packages:
        table = Table(title="Homebrew Packages")
        table.add_column("Name", style="cyan")
        table.add_column("Version")
        table.add_column("Type")
        for pkg in manifest.packages["brew"]:
            table.add_row(pkg.name, pkg.version, pkg.package_type)
        console.print(table)

    if (not category or category == "pip") and "pip" in manifest.packages:
        table = Table(title="Pip Packages")
        table.add_column("Name", style="cyan")
        table.add_column("Version")
        for pkg in manifest.packages["pip"]:
            table.add_row(pkg.name, pkg.version)
        console.print(table)

    if (not category or category == "npm") and "npm" in manifest.packages:
        table = Table(title="NPM Packages")
        table.add_column("Name", style="cyan")
        table.add_column("Version")
        for pkg in manifest.packages["npm"]:
            table.add_row(pkg.name, pkg.version)
        console.print(table)

    if (not category or category == "env_vars") and manifest.env_vars:
        table = Table(title="Environment Variables")
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_column("Config File")
        for env in manifest.env_vars:
            value = env.value if not env.value.startswith("-----") else "***"
            table.add_row(env.key, value, env.config_file)
        console.print(table)

    if (not category or category == "dotfiles") and manifest.dotfiles:
        table = Table(title="Dotfiles")
        table.add_column("Path", style="cyan")
        table.add_column("Sensitive")
        table.add_column("Encrypted")
        for df in manifest.dotfiles:
            table.add_row(df.path, "Yes" if df.sensitive else "No", "Yes" if df.encrypted else "No")
        console.print(table)

    if (not category or category == "vscode") and "vscode" in manifest.ide:
        vscode = manifest.ide["vscode"]
        table = Table(title="VS Code Extensions")
        table.add_column("Extension ID", style="cyan")
        for ext in vscode.extensions:
            table.add_row(ext)
        console.print(table)
        if vscode.settings_path:
            console.print(f"  Settings: {vscode.settings_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
