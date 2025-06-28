# LLM Instructions for Python Code Repository

## Project Overview

This is a Python project structured as an open-source repository with comprehensive testing and quality assurance practices.

## Core Principles

### Testing Requirements
- **All features must have tests**: Every new feature implementation requires corresponding test coverage
- **Bug fixes require tests**: When fixing bugs, add regression tests to `tests/` directory to prevent reoccurrence
- **Tests must pass**: All tests should pass before considering any task complete
- **Use pytest**: The project uses pytest as the testing framework

### Code Quality & Structure
- **Open-source structure**: Follow standard open-source project conventions for directory structure, documentation, and code organization
- **Pre-commit hooks**: The repository has pre-commit hooks configured - ensure code changes comply with these standards

## File Management Rules

### Strict Prohibitions
- **NEVER delete files**: Under no circumstances should you delete any files from the repository
- **NEVER commit changes**: Do not commit any changes to the repository under any circumstances

### File Deletion Protocol
- If files should be deleted, append the filename to `files_to_be_deleted.txt`
- Format: one filename per line
- The human will review and handle actual deletions

### Debug Directory
- Use the `debug/` directory for any debugging scripts or temporary testing code
- This directory is designated for experimental and diagnostic purposes

## Development Workflow

### Feature Development
1. Implement the requested feature
2. Write comprehensive tests for the feature
3. Ensure all tests pass
4. Suggest improvements (see Post-Completion section)

### Bug Fixes
1. Identify and fix the bug
2. Add regression tests to prevent the bug from reoccurring
3. Ensure all tests pass
4. Suggest improvements (see Post-Completion section)

### Test Development
- **ASK BEFORE MODIFYING CODE**: When asked to write tests, do not modify existing code without explicit permission
- **ASK BEFORE MODIFYING TESTS**: When asked to make tests pass, do not modify the test itself without explicit permission
- Focus on writing clear, comprehensive test cases

## Communication Protocol

### Seeking Permission
Always ask for permission before:
- Modifying existing code when the primary task is writing tests
- Modifying test files when the primary task is making tests pass
- Making structural changes to the project

### Post-Completion Requirements
After completing any assigned task, always:
1. Provide a summary of changes made
2. Suggest specific improvements to consider
3. Highlight any potential issues or areas for enhancement
4. Recommend next steps or related tasks

## Quality Standards

- Follow Python best practices and PEP 8 guidelines
- Ensure code is well-documented with docstrings
- Write clear, descriptive test names and assertions
- Maintain consistency with existing codebase patterns
- Consider edge cases and error handling in both code and tests

## Directory Structure Expectations

Maintain professional open-source project structure:
- Source code in appropriate modules/packages
- Tests in dedicated `tests/` directory
- Documentation files (README, etc.)
- Configuration files in root directory
- Debug scripts in `debug/` directory only
