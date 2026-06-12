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

    brew_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.BREW_FORMULA)
    pip_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.PIP_PACKAGE)
    npm_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.NPM_PACKAGE)

    assert brew_idx < pip_idx
    assert brew_idx < npm_idx

    env_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.ENV_VAR)
    dotfile_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.DOTFILE)

    assert env_idx < dotfile_idx

    ide_idx = next(i for i, s in enumerate(sorted_steps) if s.type == StepType.IDE_EXTENSION)
    assert ide_idx > pip_idx
