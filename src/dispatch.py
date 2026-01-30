
import os
import logging
from livekit import api

logger = logging.getLogger("agent")

async def create_explicit_dispatch():
    """
    Creates an explicit dispatch rule for the agent.
    Assumes that environment variables LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET are already set.
    """
    url = os.environ.get("LIVEKIT_URL")
    key = os.environ.get("LIVEKIT_API_KEY")
    secret = os.environ.get("LIVEKIT_API_SECRET")

    if not url or not key or not secret:
        logger.warning("LiveKit credentials not found in environment. Skipping creation of explicit dispatch.")
        return

    logger.info(f"Checking for existing dispatch rules using LiveKit URL: {url}...")
    
    lkapi = api.LiveKitAPI()
    
    room_name = "voice-assistant-room"
    agent_name = "agent" 
    
    try:
        # Create the dispatch rule
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name, 
                room=room_name, 
                metadata='{"agent_id": "manual-dispatch"}' 
            )
        )
        logger.info(f"SUCCESS: Created dispatch rule: {dispatch}")
    except Exception as e:
        logger.error(f"Error creating dispatch: {e}")

    try:
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
        logger.info(f"Current dispatches for room '{room_name}': {len(dispatches)}")
        for d in dispatches:
            logger.info(f" - {d}")
    except Exception as e:
        logger.error(f"Error listing dispatches: {e}")

    await lkapi.aclose()
