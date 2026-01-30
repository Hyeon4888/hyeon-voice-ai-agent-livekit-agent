from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import (
    openai,
    noise_cancellation,
)
import logging
import os
from pathlib import Path
from agent_config.get_agent import fetch_agent
from agent_config.session_factory import getAgentSession

# Load environment variables from src/.env.local
env_path = Path(__file__).parent / ".env.local"
load_dotenv(dotenv_path=env_path)
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

class Assistant(Agent):
    def __init__(self, system_prompt: str, greeting_prompt: str) -> None:
        super().__init__(instructions=system_prompt)
        self.greeting_prompt = greeting_prompt

    async def on_enter(self):
        """Called when the agent enters the room. Greets the user."""
        await self.session.generate_reply(
            instructions="Say: " + self.greeting_prompt,
            allow_interruptions=False,
        )

server = AgentServer()

@server.rtc_session()
async def my_agent(ctx: agents.JobContext):

    agent_id = ctx.job.metadata if ctx.job.metadata else None
    logger.info(f"Starting agent session for room {ctx.room.name} with agent {agent_id}")

    logger.info(f"Job metadata: {ctx.job.metadata}")

    
    await ctx.connect()
     # Wait for the first participant to join
    participant = await ctx.wait_for_participant()

    agent_id = participant.attributes.get("agent_id")
    agent = await fetch_agent(agent_id)

    if not agent:
        logger.error(f"Agent {agent_id} not found")
        return

    session = getAgentSession(agent)

    await session.start(
        room=ctx.room,
        agent=Assistant(agent.system_prompt, agent.greeting_prompt),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

if __name__ == "__main__":
    agents.cli.run_app(server)