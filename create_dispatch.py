
import asyncio
import os
from dotenv import dotenv_values
from livekit import api

async def create_explicit_dispatch():
    # Load credentials from backend .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjusted path: go up one level to reach 'backend' from 'agent-starter-python-main'
    backend_env_path = os.path.join(script_dir, "..", "backend", ".env")
    
    if not os.path.exists(backend_env_path):
        print(f"Error: Could not find {backend_env_path}")
        return

    config = dotenv_values(backend_env_path)
    
    os.environ["LIVEKIT_URL"] = config.get("LIVEKIT_URL", "")
    os.environ["LIVEKIT_API_KEY"] = config.get("LIVEKIT_API_KEY", "")
    os.environ["LIVEKIT_API_SECRET"] = config.get("LIVEKIT_API_SECRET", "")

    print(f"Using LiveKit URL: {os.environ['LIVEKIT_URL']}")
    print(f"Using API Key: ...{os.environ['LIVEKIT_API_KEY'][-4:]}")

    lkapi = api.LiveKitAPI()
    
    print("Checking for existing dispatch rules...")
    room_name = "voice-assistant-room"
    agent_name = "agent" 
    
    try:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name, 
                room=room_name, 
                metadata='{"agent_id": "manual-dispatch"}' 
            )
        )
        print("SUCCESS: Created dispatch rule:", dispatch)
    except Exception as e:
        print(f"Error creating dispatch: {e}")

    try:
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
        print(f"Current dispatches including new one: {len(dispatches)}")
        for d in dispatches:
            print(f" - {d}")
    except Exception as e:
        print(f"Error listing dispatches: {e}")

    await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(create_explicit_dispatch())
