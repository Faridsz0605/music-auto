<required_reading>
- references/conventions.md
- tests/conftest.py (existing fixtures)
- The source file being tested
</required_reading>

<process>

1. **Identify the module to test** and its public interface (functions, classes, methods).

2. **Check existing tests** in `tests/test_{module}.py` to avoid duplication.

3. **Create or extend the test file**:
   - Use `pytest` with class-based organization: `class Test{ClassName}:`
   - Each test function: `def test_{behavior}(self, ...) -> None:`
   - Add docstrings to complex tests
   - Mock all external dependencies (network, filesystem where appropriate)
   - Use fixtures from `conftest.py` (mock_ytmusic, sample_track, sample_tracks, normalized_track, config_data, config_file)

4. **Test categories to cover**:
   - **Happy path**: Normal operation with valid inputs
   - **Error paths**: Invalid inputs, missing data, network failures
   - **Edge cases**: Empty inputs, None values, boundary values
   - **Exception handling**: Verify correct exception types are raised

5. **For CLI command tests** use `typer.testing.CliRunner`:
   ```python
   from typer.testing import CliRunner
   from src.cli.main import app

   runner = CliRunner()
   result = runner.invoke(app, ["command-name", "--option", "value"])
   assert result.exit_code == 0
   ```

6. **Verify**:
   ```bash
   pytest tests/test_{module}.py -v
   pytest  # Full suite
   mypy .
   ```

</process>

<patterns>
- Use `tmp_path` fixture for filesystem tests (pytest provides it automatically)
- Use `unittest.mock.patch` for mocking module-level imports
- Use `MagicMock` for complex objects with multiple methods
- Use `pytest.raises(ExceptionType)` for exception testing
- Keep `try` blocks out of tests - let exceptions propagate naturally
</patterns>

<success_criteria>
- Tests cover all public functions/methods of the target module
- All tests pass individually and as part of the full suite
- No flaky tests (no timing dependencies, no real network calls)
- mypy passes on test files
</success_criteria>
