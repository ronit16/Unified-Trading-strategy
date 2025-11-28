from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import docker
import logging
from .db_tools import db

logger = logging.getLogger(__name__)

# --- Tool Definition ---

async def deploy_strategy_container(strategy_id: str, dockerfile_path: str, build_context: str) -> str:
    """
    Builds and runs a Docker container for the given strategy, and persists the container ID to the database.
    Returns the container ID.
    """
    try:
        client = docker.from_env()
        image_tag = f"trading-strategy:{strategy_id}"

        logger.info(f"Building Docker image for strategy {strategy_id}...")
        client.images.build(path=build_context, dockerfile=dockerfile_path, tag=image_tag)

        logger.info(f"Running Docker container for strategy {strategy_id}...")
        container = client.containers.run(image_tag, detach=True)

        # Persist the container ID to the database
        await db.add_live_strategy(strategy_id, container.id)

        logger.info(f"Container {container.id} started for strategy {strategy_id}.")
        return container.id
    except Exception as e:
        logger.error(f"Failed to deploy strategy {strategy_id}: {e}")
        return f"Error: {e}"

# --- Agent Definition ---

deployment_manager = LlmAgent(
    name="DeploymentManager",
    instruction="""You are a deployment specialist.
    1.  Read the strategy ID from `session.get('strategy_id')`.
    2.  Read the Dockerfile path from `session.get('dockerfile_path')`.
    3.  Read the build context path from `session.get('build_context')`.
    4.  Deploy the strategy as a live trading container using the `deploy_strategy_container` tool.
    5.  **Save the container ID to the session state as `session.set('container_id', ...)`**.""",
    tools=[FunctionTool(deploy_strategy_container)]
)
