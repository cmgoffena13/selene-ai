from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.main import app


def test_cli_info_prints_expected_sections(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["--info"])
    assert result.exit_code == 0
    out = result.stdout.replace("\n", "")
    assert "CLI Path:" in result.stdout
    assert "Config Directory:" in result.stdout
    assert "Ollama Model:" in result.stdout


def test_cli_version_prints_version_line(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Selene AI - Version:" in result.stdout
