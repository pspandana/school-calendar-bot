from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime

# Authenticate with Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=8080, open_browser=True)
service = build("calendar", "v3", credentials=creds)

# Search range: adjust as needed
calendar_id = 'primary'
start_date = datetime.datetime(2025, 1, 1).isoformat() + 'Z'
end_date = datetime.datetime(2026, 12, 31).isoformat() + 'Z'

# Keywords identifying bot-created school events
bot_keywords = [
    'early dismissal', 'half day', 'no school', 'teacher institute',
    'school resumes', 'spring break', 'memorial day', 'thanksgiving',
    'veterans day', 'mlk', 'labor day', 'conferences', 'independence',
    'juneteenth', 'holiday', 'last day of school', 'emergency day'
]

print("⚠️ DELETION MODE ENABLED — removing bot-created events...\n")

# Fetch events
events_result = service.events().list(
    calendarId=calendar_id,
    timeMin=start_date,
    timeMax=end_date,
    singleEvents=True,
    orderBy='startTime'
).execute()

events = events_result.get('items', [])

deleted_count = 0

for event in events:
    event_id = event['id']
    title = event.get('summary', '').lower()
    if any(keyword in title for keyword in bot_keywords):
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"🗑️ Deleting: {title} at {start}")
        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            deleted_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {title}: {e}")

print(f"\n✅ Deleted {deleted_count} event(s) from your calendar.")
