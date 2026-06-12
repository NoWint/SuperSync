from dataclasses import dataclass, field
from typing import Optional

from supersync.manifest.schema import Manifest
from supersync.provisioner.dependency import Step, StepType, topological_sort
from supersync.provisioner.conflict import ConflictDetector, ConflictType
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
        steps = []

        for pkg in self.manifest.packages.get("brew", []):
            step_type = StepType.BREW_CASK if pkg.package_type == "cask" else StepType.BREW_FORMULA
            steps.append(Step(
                type=step_type,
                name=pkg.name,
                version=pkg.version,
                source="brew",
            ))

        for pkg in self.manifest.packages.get("pip", []):
            steps.append(Step(
                type=StepType.PIP_PACKAGE,
                name=pkg.name,
                version=pkg.version,
                source="pip",
            ))

        for pkg in self.manifest.packages.get("npm", []):
            steps.append(Step(
                type=StepType.NPM_PACKAGE,
                name=pkg.name,
                version=pkg.version,
                source="npm",
            ))

        for env in self.manifest.env_vars:
            steps.append(Step(
                type=StepType.ENV_VAR,
                name=env.key,
                content=env.value,
                source="env_vars",
            ))

        for dotfile in self.manifest.dotfiles:
            steps.append(Step(
                type=StepType.DOTFILE,
                name=dotfile.path,
                content=dotfile.content,
                source="dotfiles",
                sensitive=dotfile.sensitive,
                encrypted=dotfile.encrypted,
            ))

        for ide_name, ide_config in self.manifest.ide.items():
            for ext in ide_config.extensions:
                steps.append(Step(
                    type=StepType.IDE_EXTENSION,
                    name=ext,
                    source=ide_name,
                ))
            if ide_config.settings_content:
                steps.append(Step(
                    type=StepType.VSCODE_SETTINGS,
                    name="settings.json",
                    content=ide_config.settings_content,
                    path=ide_config.settings_path,
                    source=ide_name,
                ))

        return topological_sort(steps)

    def run(self) -> RestoreReport:
        steps = self._generate_steps()
        report = RestoreReport()

        # Before executing steps, detect conflicts
        if not self.dry_run:
            detector = ConflictDetector()
            dotfile_dicts = [
                {"path": df.path, "content": df.content}
                for df in self.manifest.dotfiles
            ]
            from pathlib import Path
            conflicts = detector.detect_dotfile_conflicts(dotfile_dicts, Path.home())

            if conflicts and not self.auto_confirm:
                for conflict in conflicts:
                    console_msg = f"[yellow]Conflict:[/yellow] {conflict.message}"
                    if self.auto_confirm:
                        continue
                    # For now, auto-backup conflicting files
                    pass

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
                category_report.total += 1
                category_report.success += 1
                continue

            result = self._execute_step(step)
            category_report.add(result)

        if category_report is not None:
            report.categories.append(category_report)

        return report

    def _step_category(self, step: Step) -> str:
        mapping = {
            StepType.BREW_FORMULA: "brew",
            StepType.BREW_CASK: "brew",
            StepType.PIP_PACKAGE: "pip",
            StepType.NPM_PACKAGE: "npm",
            StepType.ENV_VAR: "env_vars",
            StepType.DOTFILE: "dotfiles",
            StepType.IDE_EXTENSION: "vscode",
            StepType.VSCODE_SETTINGS: "vscode",
        }
        return mapping.get(step.type, step.source)

    def _execute_step(self, step: Step) -> InstallResult:
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
            return self.installer.deploy_dotfile(step.name, step.content or "", backup=True)
        elif step.type == StepType.IDE_EXTENSION:
            return self.installer.install_vscode_extension(step.name)
        elif step.type == StepType.VSCODE_SETTINGS:
            return self.installer.deploy_dotfile(step.path or step.name, step.content or "")
        else:
            return InstallResult(name=step.name, status=InstallStatus.FAILED, message="Unknown step type")
