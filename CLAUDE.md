# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an **OSINT Chain-of-Verification (CoVe)** project - a verification system that uses AI models to assess the credibility of open-source intelligence through systematic verification. It uses ReAct agents with LangChain/LangGraph to perform multi-step verification with support for multiple LLM providers (OpenAI, Anthropic, Google, XAI).

## Key Commands

### Development Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Run OSINT verification**: `python3 src/osint_main.py --osint-info "..." --evidence "..." --data-path "..."`
- **Batch Excel processing**: `python3 -m src.run_examples --limit 5 --max-questions 3`
- **Async evaluation**: `python -m src.evaluation.async_evaluator --input "..." --model "o3-mini"`
- **Test imports**: `python3 src/test_imports.py`
- **Run tests**: Check individual test files in src/ (no unified test framework)

### Linting and Type Checking
**Note**: No linting or type checking commands are configured. If needed, ask the user for appropriate commands and update CLAUDE.md.

## Architecture

### Core Verification Flow
```
OSINT Info + Evidence → OSINTCOVEChain → Generate Questions → OSINTDataVerificationChain (Parallel Processing) → Credibility Assessment → Final Result
```

### Key Components
1. **OSINTCOVEChain** (`src/osint_verification_chain.py`): Main orchestrator
2. **OSINTDataVerificationChain** (`src/osint_verification_chain.py`): Core verification engine with ReAct agent
3. **ModelConfig** (`src/config.py`): Centralized multi-model configuration
4. **ExcelProcessor** (`src/excel_processing/processor.py`): Batch verification processor

### Model Configuration
All model settings are centralized in `src/config.py`. The system supports:
- OpenAI (GPT-4, o-series with reasoning effort)
- Anthropic (Claude-3 family)
- Google (Gemini models)
- XAI (Grok models)

Each verification step (question generation, react analysis, assessment, aggregation) can use different models.

### Directory Structure
```
src/
├── analysis/           # Result analysis tools
├── evaluation/         # Async evaluation framework
├── excel_processing/   # Batch processing package
├── utils/             # Data validation utilities
└── [main modules]     # Core verification logic
```

### Environment Variables
Create `.env` file with:
```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
XAI_API_KEY=...
```

## Development Guidelines

### Adding New Features
1. Check existing patterns in similar files
2. Use the established model configuration system in `config.py`
3. Follow the verification chain pattern for new verification types
4. Add appropriate CLI arguments to relevant entry points

### Working with Excel Processing
- Use `ExcelProcessor` for data preparation
- Use `CoVeEvaluator` for batch verification
- Results are saved with timestamps in specified output directory
- Supports continuation from previous runs with `--continue-from`

### Parallel Processing
- The system uses asyncio for concurrent verification
- Control concurrency with `--concurrent-tasks` parameter
- Each evidence is processed independently in parallel

### Error Handling
- The system handles various evidence formats (strings, lists, dicts)
- NaN values and empty evidence are handled gracefully
- API key validation happens at initialization