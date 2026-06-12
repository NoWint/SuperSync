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
