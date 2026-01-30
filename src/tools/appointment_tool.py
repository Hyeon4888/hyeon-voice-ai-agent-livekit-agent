import os
import logging
import dateparser
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from livekit.agents.llm import function_tool
from dotenv import load_dotenv
from livekit.agents import RunContext
from livekit.api import LiveKitAPI
from livekit.protocol.sip import TransferSIPParticipantRequest
from livekit import rtc
from tools.function_context import FunctionContext, get_function_context, log_context

load_dotenv(dotenv_path=".env.local")

logger = logging.getLogger("appointment-tools")

class AppointmentTools:
    def __init__(self):
        self._service = self._get_calendar_service()
        self._calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.api = LiveKitAPI()

    def _get_calendar_service(self):
        """Authenticates and returns the Google Calendar service object."""
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path or not os.path.exists(creds_path):
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set or file not found. Calendar integration disabled.")
            return None
        
        try:
            scopes = ['https://www.googleapis.com/auth/calendar']
            creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            return None

    @function_tool
    async def check_availability(self, date: str, time: str) -> str:
        """
        Check if a specific date and time is available for an appointment.
        args:
            date: The date to check (e.g., "Monday, January 26th")
            time: The time to check (e.g., "2:00 PM")
        """
        if not self._service:
            return "Calendar service is currently unavailable. Please try again later."

        try:
            start_dt = dateparser.parse(f"{date} {time}")
            if not start_dt:
                return f"Could not understand the date or time: {date} {time}"
            
            end_dt = start_dt + timedelta(minutes=30)
            
            events_result = self._service.events().list(
                calendarId=self._calendar_id,
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z',
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return f"Yes, {time} on {date} is available."
            else:
                return f"Sorry, {time} on {date} is already booked."
                
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return "An error occurred while checking availability."

    @function_tool
    async def book_appointment(self, ctx: RunContext,name: str, date: str, time: str) -> str:
        """
        Book an appointment for a patient.
        args:
            name: The patient's full name.
            date: The date of the appointment.
            time: The time of the appointment.
        """
        log_context(ctx)
        if not self._service:
            return "Calendar service is currently unavailable. Please try again later."

        try:
            start_dt = dateparser.parse(f"{date} {time}")
            if not start_dt:
                return f"Could not understand the date or time: {date} {time}"
            
            end_dt = start_dt + timedelta(minutes=30)

            event = {
                'summary': f'Appointment: {name}',
                'description': f'Booked via Voice Assistant. Phone: {get_function_context(ctx).phone_number}',
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC', # Adjust as needed
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC', # Adjust as needed
                },
            }

            event = self._service.events().insert(calendarId=self._calendar_id, body=event).execute()
            return f"Appointment confirmed for {name} on {date} at {time}. Link: {event.get('htmlLink')}"

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return "An error occurred while booking the appointment."

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