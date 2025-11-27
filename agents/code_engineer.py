from adk.agents import ParallelAgent, LlmAgent, SequentialAgent
from adk.tools import FunctionTool
import jinja2
import os
import pathlib
import subprocess

# --- Secure File I/O ---
SANDBOX_DIR = pathlib.Path("./generated_strategies").resolve()
SANDBOX_DIR.mkdir(exist_ok=True)

def secure_filepath(filename: str) -> pathlib.Path:
    """Resolves a filename into a secure path within the sandbox directory."""
    filepath = SANDBOX_DIR.joinpath(filename).resolve()
    if not str(filepath).startswith(str(SANDBOX_DIR)):
        raise ValueError("File path is outside of the allowed sandbox directory.")
    return filepath

# --- Tool Definitions ---

def read_template(template_path: str) -> str:
    """Reads the content of a Jinja2 template file."""
    with open(template_path, 'r') as f:
        return f.read()

def write_code_to_file(filename: str, code: str) -> str:
    """Writes the generated code to a specified file within a secure sandbox."""
    try:
        filepath = secure_filepath(filename)
        with open(filepath, 'w') as f:
            f.write(code)
        return f"Successfully wrote code to {filepath}"
    except ValueError as e:
        return str(e)

def lint_python_file(filename: str) -> str:
    """Runs flake8 on a Python file to check for syntax errors and code quality issues."""
    try:
        filepath = secure_filepath(filename)
        if not filepath.exists():
            return f"Error: File not found at {filepath}"

        result = subprocess.run(
            ["flake8", str(filepath)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return "OK"
        else:
            return result.stdout
    except ValueError as e:
        return str(e)

# --- Agent Definitions ---

# 1. StrategyCoder Agent
strategy_coder = LlmAgent(
    name="StrategyCoder",
    system_instructions="""You are a Python programmer... (instructions remain the same)""",
    tools=[
        FunctionTool(read_template),
        FunctionTool(write_code_to_file)
    ]
)

# 2. LintingAgent
linting_agent = LlmAgent(
    name="LintingAgent",
    system_instructions="""You are a code quality analyst... (instructions remain the same)""",
    tools=[FunctionTool(lint_python_file)]
)

# Sequential agent for the code-then-lint process
code_and_lint_sequence = SequentialAgent(
    name="CodeAndLint",
    agents=[
        strategy_coder,
        linting_agent
    ]
)

# 3. ConfigManager Agent
config_manager = LlmAgent(
    name="ConfigManager",
    system_instructions="""You are a configuration specialist... (instructions remain the same)""",
    tools=[FunctionTool(write_code_to_file)]
)

# 4. InfraArchitect Agent
infra_architect = LlmAgent(
    name="InfraArchitect",
    system_instructions="""You are an infrastructure expert... (instructions remain the same)""",
    tools=[FunctionTool(write_code_to_file)]
)

# --- The Main CodeEngineer Agent (Now a ParallelAgent containing a SequentialAgent) ---

code_engineer = ParallelAgent(
    name="CodeEngineer",
    agents=[
        code_and_lint_sequence, # Run the coding and linting in sequence
        config_manager,         # Run config and infra in parallel
        infra_architect
    ]
)
