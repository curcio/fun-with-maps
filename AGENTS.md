# AGENT Instructions

These guidelines apply to the entire repository for Codex agents.

## Development Guidelines
- **All features must have tests**: add coverage for every new feature.
- **Bug fixes require tests**: include regression tests in `tests/`.
- **Tests must pass**: run the full pytest suite before completion.
- **Use pytest** for all testing.
- **Open-source structure**: follow typical project organization and documentation.
- **Pre-commit hooks**: ensure changes comply with pre-commit standards.

## File Management Rules
- **NEVER delete files**. If a file should be removed, append its name to `files_to_be_deleted.txt` (one per line) for human review.
- **NEVER commit changes** to the repository.
- Use the `debug/` directory for any debugging scripts or temporary code.

## Development Workflow
### Feature Development
1. Implement the requested feature.
2. Write comprehensive tests for the feature.
3. Ensure all tests pass.
4. Suggest improvements as outlined in Post-Completion requirements.

### Bug Fixes
1. Identify and fix the bug.
2. Add regression tests to prevent reoccurrence.
3. Ensure all tests pass.
4. Suggest improvements as outlined in Post-Completion requirements.

### Test Development
- **ASK BEFORE MODIFYING CODE** when primarily asked to write tests.
- **ASK BEFORE MODIFYING TESTS** when primarily asked to make tests pass.
- Focus on clear, comprehensive test cases.

## Communication Protocol
- Ask for permission before modifying existing code if the task is focused on writing tests.
- Ask for permission before modifying test files if the task is making tests pass.
- Ask for permission before making structural changes to the project.

### Post-Completion Requirements
After completing a task, always:
1. Provide a summary of changes made.
2. Suggest specific improvements to consider.
3. Highlight any potential issues or areas for enhancement.
4. Recommend next steps or related tasks.

## Quality Standards
- Follow Python best practices and PEP 8.
- Document code with docstrings.
- Write clear, descriptive test names and assertions.
- Maintain consistency with existing code patterns.
- Consider edge cases and error handling in code and tests.

## Directory Structure Expectations
- Keep source code in appropriate modules and packages.
- Place tests in the `tests/` directory.
- Maintain documentation files (e.g., README) in the repository root.
- Keep configuration files in the root directory.
- Place debug scripts only in the `debug/` directory.
