"""Tests for XVT CLI."""

from click.testing import CliRunner

from src.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "XVT - Xiaomi Vacuum/Vale Tudo" in result.output


def test_scan_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "--help"])
    assert result.exit_code == 0
    assert "Discover Xiaomi vacuums" in result.output


def test_inject_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["inject", "--help"])
    assert result.exit_code == 0
    assert "Inject SSH key" in result.output


def test_patch_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["patch", "--help"])
    assert result.exit_code == 0
    assert "Patch firmware" in result.output


def test_version():
    """Test version is defined."""
    from src import __version__
    assert __version__ == "0.1.0"
