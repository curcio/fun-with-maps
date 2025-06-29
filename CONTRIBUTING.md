# Contributing

Thank you for wanting to contribute to **Fun with Maps**!
This project includes a CLI tool and a FastAPI backend. The following guidelines describe how to set up a development environment and how we expect contributions to be made.

## Getting Started

1. Fork and clone the repository.
2. Install the runtime requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Install development tools and the package in editable mode:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   pre-commit install
   ```
4. Run the test suite to ensure everything is working:
   ```bash
   pytest
   ```

## Development Workflow

- Make your changes in a feature branch.
- Ensure `pre-commit` passes before committing:
  ```bash
  pre-commit run --files <changed files>
  ```
- Add or update tests for any code changes.
- Verify the full test suite succeeds with `pytest`.
- Open a pull request describing your changes.

## Tools

- **pre-commit**: automatically formats code and runs linters.
- **pytest**: used for all tests.
- **uv** *(optional)*: install dependencies quickly with
  `./scripts/install_with_uv.sh`.

We appreciate your contributions!
