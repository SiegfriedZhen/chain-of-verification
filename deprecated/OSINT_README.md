# OSINT Verification Tool

This tool uses Chain-of-Verification (CoVe) methodology to verify Open Source Intelligence (OSINT) information by analyzing evidence using Python code.

## Overview

The OSINT Verification Tool allows you to:

1. Input OSINT information that needs verification
2. Provide collected evidence for analysis
3. Generate verification questions based on the claims in the OSINT information
4. Analyze the evidence using Python code
5. Assess the credibility of the OSINT information based on the verification results

## Installation

1. **Clone the Repository**
2. **Install Dependencies**: 
    ```bash
    python3 -m pip install -r requirements.txt
    ```
3. **Set Up OpenAI API Key**: 
    ```bash
    export OPENAI_API_KEY='your-api-key'
    ```

## Usage

Run the program with your OSINT information and evidence:

```bash
cd src/
python3 osint_main.py --osint-info "According to social media posts, Person X was in Location Y on Date Z" --evidence "Twitter data shows Person X posted from Location Y on Date Z. Conference attendee list includes Person X."
```

### Command-line Arguments

- `--osint-info`: The OSINT information to verify
- `--evidence`: The collected evidence to use for verification
- `--llm-name`: The OpenAI model name to use (default: "gpt-3.5-turbo")
- `--temperature`: Temperature setting for the LLM (default: 0.0)
- `--max-tokens`: Maximum tokens for LLM responses (default: 1000)
- `--show-intermediate-steps`: Show the intermediate steps of verification

## How It Works

1. **Question Template Generation**: Creates a template for verification questions
2. **Question Generation**: Generates specific verification questions based on the OSINT claims
3. **Verification Execution**: Uses Python REPL to analyze the evidence
4. **Credibility Assessment**: Evaluates which claims are verified, unverified, or contradicted

## Example

```bash
python3 osint_main.py --osint-info "According to satellite imagery, there is a military base at coordinates 37.24N, 115.81W with approximately 30 aircraft." --evidence "Satellite imagery from 2023-01-15 shows structures at 37.24N, 115.81W. Public flight tracking data shows unusual flight patterns in the area." --show-intermediate-steps
```

## Notes

- The tool uses the PythonREPLTool from langchain_experimental to execute Python code for verification
- For best results, provide detailed and structured evidence that can be analyzed programmatically
- The effectiveness of verification depends on the quality and relevance of the evidence provided 