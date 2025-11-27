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
    system_instructions="""You are a Python programmer specializing in trading algorithms.
    1.  Read the structured strategy definition from `session['strategy_json']`.
    2.  Read the Jinja2 template from `templates/strategy_template.txt` using the `read_template` tool.
    3.  Your task is to populate the template with the logic from the strategy definition.
        - The `strategy_name` should be a valid Python class name (e.g., `GoldenCrossBtc`).
        - The `indicator_calculations` should be the Python code to calculate the required indicators (e.g., `df['SMA_50'] = df['close'].rolling(window=50).mean()`).
        - The `entry_logic` and `exit_logic` should be valid Python boolean expressions based on the calculated indicators.
    4.  Generate the complete, final Python code as a string.
    5.  Save the code to a file named after the strategy (e.g., `golden_cross_btc.py`) using the `write_code_to_file` tool.
    6.  **Crucially, you must save the final filepath to the session state by setting `session['strategy_filepath']`**.""",
    tools=[
        FunctionTool(read_template),
        FunctionTool(write_code_to_file)
    ]
)

# 2. LintingAgent
linting_agent = LlmAgent(
    name="LintingAgent",
    system_instructions="""You are a code quality analyst.
    1.  Read the filepath of the generated strategy code from `session['strategy_filepath']`.
    2.  Run the linter on this file using the `lint_python_file` tool.
    3.  If the result is not 'OK', you must analyze the errors and suggest fixes to the `StrategyCoder` in the next step. For now, just report the findings.""",
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
    system_instructions="""You are a configuration specialist.
    1.  Read the strategy definition from `session['strategy_json']`.
    2.  Create a Python configuration file (e.g., `config.py`) containing the strategy's parameters, such as indicator settings, stop-loss, and take-profit levels.
    3.  Save the file using the `write_code_to_file` tool.
    4.  **Save the path to the generated config file in the session state as `session['config_filepath']`**.""",
    tools=[FunctionTool(write_code_to_file)]
)

# 4. InfraArchitect Agent
infra_architect = LlmAgent(
    name="InfraArchitect",
    system_instructions="""You are an infrastructure expert.
    1.  Read the strategy definition from `session['strategy_json']`.
    2.  Generate a `Dockerfile` suitable for running the Python trading strategy.
    3.  Generate a `docker-compose.yml` file to orchestrate the strategy container.
    4.  Save the files using the `write_code_to_file` tool.
    5.  **Save the path to the Dockerfile in the session state as `session['dockerfile_path']`**.""",
    tools=[FunctionTool(write_code_to_file)]
)

# --- The Main CodeEngineer Agent (Now a ParallelAgent containing a SequentialAgent) ---

code_engineer = ParallelAgent(
    name="CodeEngineer",
    agents=[
        code_and_lint_sequence,
        config_manager,
        infra_architect
    ]
)
