import logging
import os
import json
import httpx
from typing import Optional
from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from tools.function_context import get_function_context
from livekit.api import LiveKitAPI
from livekit.protocol.sip import TransferSIPParticipantRequest

logger = logging.getLogger("default-tools")

class DefaultTools:
    @function_tool
    async def is_org_open(self, ctx: RunContext, target_time: Optional[str] = None) -> str:
        """
        Check if the business is open currently or at a specific time.
        
        Args:
            target_time: Optional ISO format datetime string (e.g., '2023-10-27T10:00:00'). 
                         If not provided, checks the current time by first fetching server time.
        
        Returns:
            "true" if open, "false" if closed.
        """
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        secret_key = os.getenv("API_SECRET_KEY")
        
        if not secret_key:
            return "Business status is currently unavailable."

        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        # Get user_id from context (phone number)
        user_id = get_function_context(ctx).user_id
        if not user_id:
             logger.warning("No user_id found in context to use as user_id.")
             # Fallback or error? defaulting to generic check might fail if backend requires user_id
             # Proceeding hoping backend handles it or we return error.
             # Based on previous code, user_id was required.
        
        try:
            async with httpx.AsyncClient() as client:
                # If no time provided, fetch server time first
                if not target_time:
                    time_url = f"{api_url}/agent/is-org-open/time"
                    response = await client.get(time_url, headers=headers)
                    response.raise_for_status()
                    target_time = response.json().get("current_time")
                    if not target_time:
                         return "Unable to determine current server time."

                # Check status for the specific time
                check_url = f"{api_url}/agent/is-org-open/check"
                params = {
                    "user_id": user_id,
                    "target_time": target_time
                }
                
                response = await client.get(check_url, headers=headers, params=params)
                response.raise_for_status()
                is_open = response.json()
                
                result = {
                    "status": "open" if is_open else "closed",
                    "timestamp": target_time,
                }
                return json.dumps(result)

        except Exception as e:
            logger.error(f"Error checking business status: {e}")
            return json.dumps({
                "status": "error", 
                "message": "Unable to check business status.",
                "error": str(e)
            })

    
    @function_tool
    async def call_forward(self, ctx: RunContext) -> str:
        """
        Forwards the current call to another phone number.
    
        """
        function_context = get_function_context(ctx)
        room_name = function_context.room_name
        participant = function_context.participant

        if not room_name or not participant:
            return "Could not find room or participant."
        
        async with LiveKitAPI() as livekit_api:
            transfer_to = 'tel:+12894898478'

            try:
                # Create transfer request
                transfer_request = TransferSIPParticipantRequest(
                    participant_identity=participant.identity,
                    room_name=room_name,
                    transfer_to=transfer_to,
                    play_dialtone=False
                )
                logger.debug(f"Transfer request: {transfer_request}")
          
                # Transfer caller
                await livekit_api.sip.transfer_sip_participant(transfer_request)
                print("SIP participant transferred successfully")
          
            except Exception as error:
                # Check if it's a Twirp error with metadata
                if hasattr(error, 'metadata') and error.metadata:
                    print(f"SIP error code: {error.metadata.get('sip_status_code')}")
                    print(f"SIP error message: {error.metadata.get('sip_status')}")
                else:
                    print(f"Error transferring SIP participant:")
                    print(f"{error.status} - {error.code} - {error.message}")
