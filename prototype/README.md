# GitHub Documentation Analyzer - Prototype

This is a modularized version of the original `github_docs.py` file, broken down into smaller, manageable components.

## Structure

- `config.py` - Configuration and constants
- `models/` - Data models and schemas
- `parsers/` - Code parsing utilities
- `analyzers/` - Analysis engines
- `llm/` - LLM integration and processing
- `utils/` - Utility functions
- `main.py` - Main orchestration script

## Original File Size
- **Multiple responsibilities** - Parsing, analysis, LLM processing, etc.

## Benefits of Modularization
- **Easier maintenance** - Each module has a single responsibility
- **Better testing** - Individual components can be tested separately
- **Improved readability** - Smaller files are easier to understand
- **Reusability** - Components can be reused in other projects