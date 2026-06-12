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

    console.print(Panel(f"Environment from [cyan]{manifest.hostname}[/cyan] ({manifest.platform}/{manifest.arch})", title="Manifest"))

    engine = ProvisionerEngine(manifest, dry_run=dry_run, auto_confirm=yes)
    report = engine.run()

    console.print(report.format())
    logger.info("Restore completed from %s", file_path)


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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
