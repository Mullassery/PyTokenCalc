"""Tests for quick CLI."""

import json
import subprocess
import sys


def test_quick_cli_basic_count():
    """Test basic token counting via quick CLI."""
    result = subprocess.run(
        [sys.executable, "-m", "pytokencalc.quick_cli", "Hello world"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Should have "tokens" in output
    assert "tokens" in result.stdout


def test_quick_cli_json_output():
    """Test JSON output mode."""
    result = subprocess.run(
        [sys.executable, "-m", "pytokencalc.quick_cli", "-j", "Hello world"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    # Parse JSON output
    output = json.loads(result.stdout.strip())
    assert "tokens" in output
    assert "model" in output
    assert output["model"] == "gpt-4"
    assert isinstance(output["tokens"], int)
    assert output["tokens"] > 0


def test_quick_cli_model_specification():
    """Test specifying a model."""
    result = subprocess.run(
        [sys.executable, "-m", "pytokencalc.quick_cli", "-m", "gpt-4", "test"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "tokens" in result.stdout


def test_quick_cli_help():
    """Test help output."""
    result = subprocess.run(
        [sys.executable, "-m", "pytokencalc.quick_cli", "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pycount" in result.stdout
    assert "USAGE" in result.stdout


def test_quick_cli_no_text():
    """Test with no text input (should show help)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytokencalc.quick_cli"],
        capture_output=True,
        text=True,
    )
    # Should print help or exit with error
    assert result.returncode != 0 or "USAGE" in result.stdout
