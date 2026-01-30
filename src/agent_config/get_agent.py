import os
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

from pathlib import Path

# Load environment variables
load_dotenv(".env.local")

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

@dataclass
class Agent:
    id: str
    name: str = "Assistant"
    agent_type: str = "realtime"
    voice: str = "alloy"
    greeting_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    api_key: Optional[str] = None
    tool_id: Optional[str] = None

@dataclass
class AgentTool:
    id: str
    name: str
    appointment_tool: bool
    user_id: str
    created_at: str

async def fetch_agent(agent_id: str) -> Agent:
    """
    Fetch agent configuration from the backend API.
    
    Args:
        agent_id: The ID of the agent to fetch.
        
    Returns:
        Agent: The agent configuration object.
        
    Raises:
        ValueError: If API_SECRET_KEY is not set.
        httpx.HTTPStatusError: If the API request fails.
    """
    
    # Get API configuration
    api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
    secret_key = os.getenv("API_SECRET_KEY")
    
    if not secret_key:
        raise ValueError("API_SECRET_KEY is not set in environment variables")
    
    # Construct endpoint URL
    url = f"{api_url}/agents/get/{agent_id}"
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Map fields if necessary, assuming API returns keys matching Agent fields
        # Ideally, we should validate this, but for now strict mapping
        api_key = data.get("api_key")
        logger.info(f"API Key: {api_key}")
        logger.info(f"Agent: {data.get('name')}")
        logger.info(f"Agent Type: {data.get('agent_type')}")
        logger.info(f"Voice: {data.get('voice')}")
        logger.info(f"Greeting Prompt: {data.get('greeting_prompt')}")
        logger.info(f"System Prompt: {data.get('system_prompt')}")
        logger.info(f"User ID: {data.get('user_id')}")

        return Agent(
            id=data.get("id", "manual-dispatch"),
            name=data.get("name", "Assistant"),
            agent_type=data.get("agent_type", "realtime"), # Ensure backend sends this or default
            voice=data.get("voice", "alloy"),
            greeting_prompt=data.get("greeting_prompt",""),
            system_prompt=data.get("system_prompt",""),
            user_id=data.get("user_id",""),
            api_key=data.get("api_key"),
            tool_id=data.get("tool_id")
        )

async def get_tools(tool_id: str) -> AgentTool:
    """
    Fetch tool configuration from the backend API.
    
    Args:
        tool_id: The ID of the tools to fetch.
        
    Returns:
        AgentTool: The tools configuration object.
        
    Raises:
        ValueError: If API_SECRET_KEY is not set.
        httpx.HTTPStatusError: If the API request fails.
    """
    
    # Get API configuration
    api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
    secret_key = os.getenv("API_SECRET_KEY")
    
    if not secret_key:
        raise ValueError("API_SECRET_KEY is not set in environment variables")
    
    # Construct endpoint URL
    url = f"{api_url}/tools/get/{tool_id}"
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    
        logger.info(f"Tool ID: {data.get('id')}")
        logger.info(f"Tool Name: {data.get('name')}")
        logger.info(f"Appointment Tool: {data.get('appointment_tool')}")
        logger.info(f"User ID: {data.get('user_id')}")

        return AgentTool(
            id=data.get("id"),
            name=data.get("name"),
            appointment_tool=data.get("appointment_tool"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at")
        )

# Import necessary for the new function
from tools.appointment_tool import AppointmentTools

async def get_agentTools(agent: Agent) -> list:
    """
    Fetch and initialize tools for the agent.
    """
    tools = []
    if agent.tool_id:
        try:
            agent_tools_config = await get_tools(agent.tool_id)
            if agent_tools_config.appointment_tool:
                logger.info(f"Registering appointment tools for agent {agent.id}")
                appt_tools = AppointmentTools()
                tools.extend([
                    appt_tools.check_availability,
                    appt_tools.book_appointment,
                    appt_tools.call_forward
                ])
        except Exception as e:
            logger.error(f"Failed to fetch tools for agent {agent.id}: {e}")
    return tools

async def create_history(data: dict) -> None:
    """
    Create a history entry in the backend.
    
    Args:
        data: Dictionary containing history data matching HistoryCreate model.
    """
    api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
    secret_key = os.getenv("API_SECRET_KEY")
    
    if not secret_key:
        logger.warning("API_SECRET_KEY not set, skipping history creation")
        return

    url = f"{api_url}/history/create"
    
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Sending history creation request to {url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to create history. Status: {response.status_code}, Response: {response.text}")
            response.raise_for_status()
            logger.info(f"History created successfully for agent {data.get('agent_id')}")
    except Exception as e:
        logger.error(f"Exception during history creation: {e}", exc_info=True)
