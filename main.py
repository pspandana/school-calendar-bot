import os
from dotenv import load_dotenv
import pdfplumber
from datetime import datetime, timedelta
import dateparser

# 1. Load API Key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise Exception("Missing OPENAI_API_KEY")

# 2. Split PDF Columns and Extract Text
pdf_path = "school_calendar.pdf"
left_text = ""
right_text = ""

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        width = page.width
        height = page.height

        # Left column
        left = page.within_bbox((0, 0, width / 2, height))
        if left:
            left_text += left.extract_text() + "\n"

        # Right column
        right = page.within_bbox((width / 2, 0, width, height))
        if right:
            right_text += right.extract_text() + "\n"

full_text = left_text + "\n" + right_text

# 3. GPT: Extract Events
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

calendar_text = full_text[:3000]  # Limit to stay within token limit

prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are an assistant that extracts school calendar events.
Return each event in this format:

- Event: <Event Name>
  Date: <Date or date range like 2025-08-10 to 2025-08-12 or comma-separated list>
  Time: <Time like '9:00 AM - 2:00 PM' or 'All day'>
  Description: <Optional extra details>

Text:
{text}
"""
)

llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0, model_name="gpt-4")
chain = LLMChain(llm=llm, prompt=prompt)
events_output = chain.run(text=calendar_text)

print("\n📅 Extracted Events:")
print(events_output)

# 4. Google Calendar Auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=8080, open_browser=True)
service = build("calendar", "v3", credentials=creds)

# 5. Parse and Add Events
print("\n📤 Adding Events to Calendar...")

from googleapiclient.errors import HttpError

print("\n📤 Adding Events to Calendar (no duplicates)...")

for block in events_output.strip().split("- Event:"):
    if not block.strip():
        continue

    try:
        lines = block.strip().splitlines()
        print("🔍 RAW LINES:", lines)

        title = lines[0].strip()

        date_line = next((line for line in lines if line.strip().lower().startswith("date:")), None)
        if not date_line:
            print("⚠️ Skipping: Missing date line")
            continue
        date_value = date_line.split(":", 1)[1].strip()

        time_line = next((line for line in lines if line.strip().lower().startswith("time:")), None)
        time_value = time_line.split(":", 1)[1].strip() if time_line and ":" in time_line else "All day"

        description_line = next((line for line in lines if line.strip().lower().startswith("description:")), None)
        description = description_line.split(":", 1)[1].strip() if description_line else ""

        # Handle multiple dates
        raw_dates = []
        if "to" in date_value:
            start_str, end_str = date_value.split("to")
            start = dateparser.parse(start_str.strip())
            end = dateparser.parse(end_str.strip())
            current = start
            while current <= end:
                raw_dates.append(current)
                current += timedelta(days=1)
        elif "," in date_value:
            raw_dates = [dateparser.parse(d.strip()) for d in date_value.split(",")]
        else:
            raw_dates = [dateparser.parse(date_value)]

        for event_date in raw_dates:
            if not event_date:
                print(f"⚠️ Skipping invalid date in: {date_value}")
                continue

            # Set default times
            if "early dismissal" in time_value.lower():
                start_time = "09:00"
                end_time = "14:00"
            elif "half" in time_value.lower():
                start_time = "09:00"
                end_time = "12:00"
            elif time_value.lower() == "all day":
                start_time = "09:00"
                end_time = "17:00"
            else:
                start_time = "09:00"
                end_time = "17:00"

            start_dt = datetime.combine(event_date.date(), datetime.strptime(start_time, "%H:%M").time())
            end_dt = datetime.combine(event_date.date(), datetime.strptime(end_time, "%H:%M").time())

            # 🔍 Check for duplicate
            iso_start = start_dt.isoformat() + "-05:00"  # Adjust time zone
            iso_end = end_dt.isoformat() + "-05:00"

            existing = service.events().list(
                calendarId='primary',
                timeMin=iso_start,
                timeMax=iso_end,
                q=title,
                singleEvents=True
            ).execute()

            if any(title.lower() in event['summary'].lower() for event in existing.get('items', [])):
                print(f"⏭️ Skipped duplicate: {title} on {event_date.date()}")
                continue

            # ✅ Insert
            event = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "America/Chicago"
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "America/Chicago"
                },
                "attendees": [
                    {"email": "sai.k.ramadugu@gmail.com"}  # Optional
                ]
            }

            service.events().insert(calendarId='primary', body=event).execute()
            print(f"✅ Added: {title} on {event_date.date()}")

    except HttpError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Skipped event due to error: {e}")
        print("⚠️ Block:", block)
