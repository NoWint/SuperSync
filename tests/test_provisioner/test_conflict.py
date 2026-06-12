from supersync.provisioner.conflict import ConflictDetector, Conflict, ConflictType


def test_detect_dotfile_conflict(tmp_path):
    detector = ConflictDetector()

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
