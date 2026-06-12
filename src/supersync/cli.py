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
