from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, JobContext, cli,WorkerOptions,JobProcess
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
import logging
import os
from pathlib import Path
import datetime
from agent_config.get_agent import fetch_agent, get_agentTools, create_history
from agent_config.session_factory import getAgentSession
from agent_config.create_session_report import create_SessionReport
from tools.function_context import FunctionContext

# Load environment variables from src/.env.local
load_dotenv(".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

class Assistant(Agent):
    def __init__(self, system_prompt: str, greeting_prompt: str, tools: list = None) -> None:
        super().__init__(instructions=system_prompt, tools=tools)
        self.greeting_prompt = greeting_prompt

    async def on_enter(self):
        """Called when the agent enters the room. Greets the user."""
        await self.session.generate_reply(
            instructions="before you say anything, check if user is calling during the business hours and if so forward the call to the agent otherwise say: " + self.greeting_prompt,
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    """Prewarm VAD model for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx:JobContext):

    agent_id = ctx.job.metadata if ctx.job.metadata else None
    logger.info(f"Starting agent session for room {ctx.room.name} with agent {agent_id}")

    logger.info(f"Job metadata: {ctx.job.metadata}")

    
    await ctx.connect()
     # Wait for the first participant to join
    participant = await ctx.wait_for_participant()

    is_sip_participant = (
        participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP or
        "sip.callID" in participant.attributes  # Fallback: check for SIP attributes
    )

    caller_phone_number = "Unknown"
    if is_sip_participant:
        caller_phone_number = participant.attributes.get("sip.phoneNumber", "Unknown")

    logger.info(f"Room name: {ctx.room.name}, Room SID: {ctx.room.sid}")
    logger.info(f"Participant identity: {participant.identity}, Name: {participant.name}, Kind: {participant.kind}")
    logger.info(f"Participant attributes: {participant.attributes}")

    agent_id = participant.attributes.get("agent_id") or ctx.job.metadata
    agent = await fetch_agent(agent_id)

    if not agent:
        logger.error(f"Agent {agent_id} not found")
        return

    session = getAgentSession(agent)

    tools = await get_agentTools(agent)

    start_time = datetime.datetime.now()

    session.function_context = FunctionContext(
        phone_number=caller_phone_number,
        room_name=ctx.room.name,
        participant=participant,
        user_id=agent.user_id,
    )

    async def shutdown_handler():
        logger.info(f"Session shutdown initiated for agent {agent.id}")
        end_time = datetime.datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Use make_session_report to capture session details including conversation history

        conversation = create_SessionReport(ctx, session)
        
        logger.info(f"Gathered session history: duration={duration}s, conversation_messages={len(conversation)}")
        
        await create_history({
            "agent_id": agent.id,
            "date": start_time.date().isoformat(),
            "time": start_time.time().isoformat(),
            "duration": duration,
            "summary": None,
            "conversation": conversation
        })

    ctx.add_shutdown_callback(shutdown_handler)

    my_assistant = Assistant(agent.system_prompt, agent.greeting_prompt, tools=tools)

    await session.start(
        room=ctx.room,
        agent=my_assistant,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        prewarm_fnc=prewarm, 
        agent_name='voice-ai-agent'
    ))