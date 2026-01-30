from livekit.agents import AgentSession, inference
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from .get_agent import Agent

def getAgentSession(agent: Agent) -> AgentSession:
    """
    Creates and returns an AgentSession based on the agent configuration type.
    
    Args:
        agent: Agent configuration object.
                      
    Returns:
        AgentSession: Configured agent session.
    """
    
    if agent.agent_type == "realtime":
        return AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice=agent.voice,
                api_key=agent.api_key,
            ),
            vad=silero.VAD.load(),
        )
    if agent.agent_type == "custom":
        return AgentSession(
            # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
            # See all available models at https://docs.livekit.io/agents/models/stt/
            stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
            # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
            # See all available models at https://docs.livekit.io/agents/models/llm/
            llm=inference.LLM(model="openai/gpt-4.1-mini"),
            # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
            # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
            tts=inference.TTS(
                model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
            ),
            # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
            # See more at https://docs.livekit.io/agents/build/turns
            turn_detection=MultilingualModel(),
            vad=silero.VAD.load(),
            # allow the LLM to generate a response while waiting for the end of turn
            # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
            preemptive_generation=True,
        )

    # Fallback default
    return AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice=agent.voice or "alloy",
            api_key=agent.openai_api_key,
        ),
        vad=silero.VAD.load(),
    )
