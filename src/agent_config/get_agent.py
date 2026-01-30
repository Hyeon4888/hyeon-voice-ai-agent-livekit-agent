import os
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(dotenv_path=env_path)

@dataclass
class Agent:
    id: str
    name: str = "Assistant"
    agent_type: str = "realtime"
    voice: str = "alloy"
    greeting_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None

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
        return Agent(
            id=data.get("id", "manual-dispatch"),
            name=data.get("name", "Assistant"),
            agent_type=data.get("agent_type", "realtime"), # Ensure backend sends this or default
            voice=data.get("voice", "alloy"),
            greeting_prompt=data.get("greeting_prompt",""),
            system_prompt=data.get("system_prompt",""),
            user_id=data.get("user_id","")
        )
