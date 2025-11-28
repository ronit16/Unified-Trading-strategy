# Autonomous Algorithmic Trading Ecosystem

This project implements a complete, multi-phase autonomous trading system using the Google Agent Development Kit (ADK). The system is designed to research, engineer, backtest, deploy, and monitor algorithmic trading strategies automatically.

It uses a microservices-based architecture leveraging:
- **Google Agent Development Kit (ADK):** For agent orchestration.
- **NATS:** For high-performance, distributed messaging.
- **PostgreSQL:** For data persistence and state management.

## Prerequisites

Before you begin, ensure you have the following installed:
- [Docker](https://www.docker.com/get-started) and Docker Compose
- [Python 3.10+](https://www.python.org/downloads/)
- An active Google Cloud Platform (GCP) project with the AI Platform APIs enabled.

## Setup instruction

Follow these steps to get the application running.

### 1. Configure Environment Variables

The application requires API keys and configuration settings to be stored in a `.env` file.

First, copy the example file:
```bash
cp .env.example .env
```

Next, edit the `.env` file with your specific credentials:
```
# .env

# Google Cloud
GOOGLE_PROJECT_ID="your-gcp-project-id"
GOOGLE_API_KEY="your-google-api-key"

# NATS
NATS_URL="nats://localhost:4222"

# PostgreSQL
DB_URL="postgresql://admin:password@localhost:5432/trading_bot"
```
- Replace `"your-gcp-project-id"` and `"your-google-api-key"` with your actual Google Cloud credentials.

### 2. Start Infrastructure Services

The required services (NATS and PostgreSQL) are managed via Docker. Start them with the following command:
```bash
docker-compose up -d
```
This will start both containers in the background. You can verify they are running with `docker ps`.

### 3. Install Python Dependencies

Install all the necessary Python libraries using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

## Running the Application

Once the setup is complete, you can start the autonomous trading system with a single command:

```bash
python main.py
```

This will launch both the `AlphaFactory` agent workflow and the persistent `MonitoringAgent` concurrently. You can view the system's activity and logs in the `trading_bot.log` file and in your console.

## How It Works

The system executes the following automated workflow:

1.  **Strategy Research:** The `StrategyResearcher` agent searches the web to find trading strategies for a given asset (e.g., Bitcoin).
2.  **Code Engineering:** The `CodeEngineer` agent takes the structured strategy and generates all necessary files in the `generated_strategies/` directory, including the Python strategy code, configuration files, and a Dockerfile. It also runs a linter to ensure code quality.
3.  **Optimization:** The `StrategyOptimizer` agent takes the generated code and runs it through a backtesting loop, analyzing the results and refining parameters to improve performance.
4.  **Deployment:** Once a strategy is deemed profitable, the `DeploymentManager` agent packages it into a Docker container and deploys it for live trading.
5.  **Monitoring:** A persistent `MonitoringAgent` listens to NATS telemetry from all live strategies, ready to send alerts or intervene if performance degrades or errors occur.
