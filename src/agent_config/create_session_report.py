from livekit import agents

def create_SessionReport(ctx: agents.JobContext, session):
    # Use make_session_report to capture session details including conversation history
    session_report = ctx.make_session_report(session)
    report_dict = session_report.to_dict()
    
    # Filter events to get conversation messages and function calls
    events = report_dict.get("events", [])
    conversation = []
    for event in events:
        if event.get("type") == "conversation_item_added":
            conversation.append(event.get("item", {}))
        elif event.get("type") == "function_tools_executed":
            conversation.append(event)
            
    return conversation
