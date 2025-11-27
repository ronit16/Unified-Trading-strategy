from adk.agents import LoopAgent, LlmAgent
from adk.tools import FunctionTool
import subprocess
from .db_tools import save_backtest_results_tool
from .code_engineer import write_code_to_file # Re-using the secure file writer

# --- Tool Definitions ---

def run_backtest_script(strategy_file: str, config_file: str) -> str:
    """
    Executes the backtesting script... (tool remains the same)
    """
    # ... (implementation unchanged)

# --- Agent Definitions ---

# 1. BacktestRunner Agent
backtest_runner = LlmAgent(
    name="BacktestRunner",
    system_instructions="""Your job is to run the backtest... (instructions remain the same)""",
    tools=[FunctionTool(run_backtest_script)]
)

# 2. ResultAnalyzer Agent
result_analyzer = LlmAgent(
    name="ResultAnalyzer",
    system_instructions="""You are a quantitative analyst... (instructions remain the same)""",
    tools=[save_backtest_results_tool]
)

# 3. ParameterUpdater Agent
parameter_updater = LlmAgent(
    name="ParameterUpdater",
    system_instructions="""You are a configuration engineer.
    1.  Read the new parameters from `session['new_params']`.
    2.  Read the config filepath from `session['config_filepath']`.
    3.  Update the config file with the new parameters.""",
    tools=[FunctionTool(write_code_to_file)] # Re-using the secure file writer
)

# --- The Main LoopAgent ---

strategy_optimizer = LoopAgent(
    name="StrategyOptimizer",
    agents=[
        backtest_runner,
        result_analyzer,
        parameter_updater # Add the updater to the loop
    ],
    max_iterations=3
)
