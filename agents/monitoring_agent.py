from google.adk.agents import BaseAgent
from google.adk.tools import FunctionTool
from pydantic import PrivateAttr
from typing import Any, Dict
import nats
import docker
import logging
import asyncio
import json
from decouple import config
from pyparsing import Dict
from .db_tools import db

logger = logging.getLogger(__name__)

# --- Tool Definitions ---

async def stop_strategy_container(container_id: str) -> str:
    """Stops a running Docker container in a non-blocking way."""
    def _stop_container():
        """Synchronous function to be run in a thread."""
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
            container.stop()
            logger.info(f"Successfully stopped container {container_id}.")
            return f"Successfully stopped container {container_id}."
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return f"Error stopping container {container_id}: {e}"

    return await asyncio.to_thread(_stop_container)

async def send_alert(message: str) -> str:
    """Sends an alert to a human operator (placeholder)."""
    logger.warning(f"ALERT: {message}")
    return "Alert sent."

# --- Agent Definition ---

class MonitoringAgent(BaseAgent):
    """
    A long-running agent that monitors live trading strategies via NATS.
    """
    # 2. DECLARE FIELDS HERE using PrivateAttr
    # This tells Pydantic: "Let me store this data, but don't validate it or save it to JSON."
    _nc: Any = PrivateAttr(default=None)
    _strategy_to_container: Dict = PrivateAttr(default_factory=dict)

    def __init__(self):
        super().__init__(name="MonitoringAgent")
        # You no longer need to set self.nc = None here; PrivateAttr handles the default.

    async def _run_agent(self, session):
        logger.info("Starting MonitoringAgent...")
        await self.load_live_strategies()
        await self.connect_to_nats()

        # Update variable access to use the underscore version
        await self._nc.subscribe("telemetry.live.*", cb=self.on_telemetry_message)

        while True:
            await asyncio.sleep(1)

    async def load_live_strategies(self):
        # Update variable access
        self._strategy_to_container = await db.get_live_strategies()
        logger.info(f"Loaded {len(self._strategy_to_container)} live strategies.")

    async def connect_to_nats(self):
        try:
            # Update variable access
            self._nc = await nats.connect(config('NATS_URL'))
            logger.info("MonitoringAgent connected to NATS.")
        except Exception as e:
            logger.error(f"MonitoringAgent failed to connect to NATS: {e}")
            raise

    async def on_telemetry_message(self, msg):
        subject = msg.subject
        strategy_id = subject.split('.')[-1]
        data = json.loads(msg.data.decode())

        logger.info(f"Received telemetry for strategy {strategy_id}: {data}")

        # Update variable access
        container_id = self._strategy_to_container.get(strategy_id)
        if not container_id:
            logger.warning(f"Received telemetry for unknown strategy {strategy_id}")
            return

        if data.get("status") == "ERROR":
            await send_alert(f"Strategy {strategy_id} reported an error: {data.get('message')}")

        if data.get("drawdown", 0) > 0.2:
            await send_alert(f"Strategy {strategy_id} has breached its drawdown limit.")
            await stop_strategy_container(container_id)

monitoring_agent = MonitoringAgent()