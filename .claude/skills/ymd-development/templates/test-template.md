<template name="test-file">

## File: tests/test_{module}.py

```python
"""Tests for src/{path}/{module}.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from src.{path}.{module} import {function_or_class}


class Test{ClassName}:
    """Tests for {ClassName}."""

    def test_happy_path(self) -> None:
        """Test normal operation with valid inputs."""
        # Arrange
        # Act
        result = {function_or_class}(...)
        # Assert
        assert result == expected

    def test_error_handling(self) -> None:
        """Test behavior with invalid inputs."""
        with pytest.raises({ExpectedException}):
            {function_or_class}(invalid_input)

    def test_edge_case(self) -> None:
        """Test boundary conditions."""
        result = {function_or_class}(edge_input)
        assert result == expected_edge_result
```

## CLI Command Test Template

```python
"""Tests for CLI command: {command}."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestCli{Command}:
    """Tests for the {command} CLI command."""

    @patch("src.cli.commands.{command}.load_auth")
    @patch("src.cli.commands.{command}.load_config")
    def test_success(self, mock_config: MagicMock, mock_auth: MagicMock) -> None:
        """Test successful command execution."""
        mock_config.return_value = MagicMock(download_dir=Path("downloads"))
        result = runner.invoke(app, ["{command}"])
        assert result.exit_code == 0

    def test_auth_failure(self) -> None:
        """Test command behavior when auth fails."""
        with patch("src.cli.commands.{command}.load_auth", side_effect=AuthenticationError("No credentials")):
            result = runner.invoke(app, ["{command}"])
            assert result.exit_code == 1
```

</template>
