from adk.agents import LoopAgent, LlmAgent
from adk.tools import FunctionTool
import subprocess
import json
from .db_tools import save_backtest_results_tool
from .code_engineer import write_code_to_file

# --- Tool Definitions ---

def run_backtest_script(strategy_filepath: str, config_filepath: str, csv_datapath: str) -> str:
    """
    Executes the backtesting logic from the main script with the specified files.
    Returns a JSON string containing the backtest performance metrics.
    """
    command = [
        "python", "main.py",
        "--mode", "BACKTEST",
        "--strategy_filepath", strategy_filepath,
        "--config_filepath", config_filepath,
        "--csv_datapath", csv_datapath
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # The last line of stdout should be the JSON results
        output_lines = result.stdout.strip().split('\n')
        return output_lines[-1]
    except subprocess.CalledProcessError as e:
        return f"Backtest failed with error: {e.stderr}"
    except (json.JSONDecodeError, IndexError) as e:
        return f"Failed to parse backtest results from stdout: {e}. Full output: {result.stdout}"

# --- Agent Definitions ---

# 1. BacktestRunner Agent
backtest_runner = LlmAgent(
    name="BacktestRunner",
    system_instructions="""Your job is to run the backtest for the given strategy.
    1.  Read the strategy filepath from `session['strategy_filepath']`.
    2.  Read the config filepath from `session['config_filepath']`.
    3.  Read the path to the historical data CSV from `session['csv_datapath']`.
    4.  Execute the backtest using the `run_backtest_script` tool.
    5.  **Save the JSON results of the backtest to the session state as `session['backtest_results_json']`**.""",
    tools=[FunctionTool(run_backtest_script)]
)

# 2. ResultAnalyzer Agent
result_analyzer = LlmAgent(
    name="ResultAnalyzer",
    system_instructions="""You are a quantitative analyst. Your task is to interpret backtest results.
    1.  Read the backtest results JSON from `session['backtest_results_json']`.
    2.  The results contain metrics like 'sharpe_ratio', 'max_drawdown', and 'final_equity'.
    3.  Your success criterion is a `sharpe_ratio` greater than 1.5.
    4.  If the criterion is met, you must set `session['optimization_complete'] = True` to exit the loop.
    5.  If the criterion is NOT met, you must propose a single, specific parameter change to improve performance.
    6.  **You must save your suggestion as a JSON object to `session['new_params']`**. For example: `{'stop_loss_pct': 3.0}`.
    7.  Finally, you must always save the results to the database using the `save_backtest_results_tool`.""",
    tools=[save_backtest_results_tool]
)

# 3. ParameterUpdater Agent
parameter_updater = LlmAgent(
    name="ParameterUpdater",
    system_instructions="""You are a configuration engineer.
    1.  Check if `session.get('optimization_complete', False)` is True. If it is, your job is done and you should do nothing.
    2.  If it is not complete, read the new parameters from `session['new_params']`.
    3.  Read the config filepath from `session['config_filepath']`.
    4.  Load the existing config file as a string, update the specific parameter value, and write the modified string back to the config file using the `write_code_to_file` tool.""",
    tools=[FunctionTool(write_code_to_file)]
)

# --- The Main LoopAgent ---

strategy_optimizer = LoopAgent(
    name="StrategyOptimizer",
    agents=[
        backtest_runner,
        result_analyzer,
        parameter_updater
    ],
    max_iterations=3
)
