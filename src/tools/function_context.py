import json
import logging
from dataclasses import dataclass
from livekit import rtc
from livekit.agents import RunContext

logger = logging.getLogger("function-context")

@dataclass
class FunctionContext:
    phone_number: str
    room_name: str
    participant: rtc.RemoteParticipant

def get_function_context(ctx: RunContext) -> FunctionContext:
    return getattr(ctx.session, "function_context", FunctionContext("", "", None))

def log_context(ctx: RunContext):
    fn_ctx = get_function_context(ctx)
    

    data = {
        "phone_number": fn_ctx.phone_number,
        "room_name": fn_ctx.room_name
    }
    
    logger.info(f"Function Context:\n{json.dumps(data, indent=2)}")
