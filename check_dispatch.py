
import asyncio
import os
from dotenv import dotenv_values
from livekit import api

async def check_dispatch():
    # Load credentials from backend .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_env_path = os.path.join(script_dir, "..", "backend", ".env")
    
    if not os.path.exists(backend_env_path):
        print(f"Error: Could not find {backend_env_path}")
        return

    config = dotenv_values(backend_env_path)
    
    os.environ["LIVEKIT_URL"] = config.get("LIVEKIT_URL", "")
    os.environ["LIVEKIT_API_KEY"] = config.get("LIVEKIT_API_KEY", "")
    os.environ["LIVEKIT_API_SECRET"] = config.get("LIVEKIT_API_SECRET", "")

    lkapi = api.LiveKitAPI()
    room_name = "voice-assistant-room"
    
    print(f"Checking dispatch rules for room: {room_name}")

    try:
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
        print(f"Found {len(dispatches)} dispatch rules.")
        for d in dispatches:
            print(f" - ID: {d.id}, Agent: {d.agent_name}, Room: {d.room}")
    except Exception as e:
        print(f"Error listing dispatches: {e}")

    await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(check_dispatch())
