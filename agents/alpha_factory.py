from google.adk.agents import SequentialAgent
from .strategy_researcher import strategy_researcher
from .code_engineer import code_engineer
from .strategy_optimizer import strategy_optimizer
from .deployment_manager import deployment_manager

# --- The Root "Alpha Factory" Agent ---

alpha_factory = SequentialAgent(
    name="AlphaFactory",
    sub_agents=[
        strategy_researcher,
        code_engineer,
        strategy_optimizer,
        deployment_manager
    ]
)
