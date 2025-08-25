# 📅 School Calendar Bot — Easy Setup Guide

Hey there! 👋  
This bot helps you **automatically read school calendar PDFs** and add important dates (like holidays, early dismissals, half days) directly into your **Google Calendar**. You can even invite someone, like your spouse, to events.

## ✅ What it does:
- Reads your school calendar PDF.
- Picks out events like "Half Day", "No School", etc.
- Adds those events into your Google Calendar with correct times.
- Lets you invite others to events (like your husband).

---

## 🛠️ Setup Instructions

### 1. Clone or Download This Project
Download this folder to your computer.

### 2. Create a Google Cloud Project
You only need to do this once:
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable the **Google Calendar API**
- Download `credentials.json` and place it in this folder

### 3. Add Your Environment File
Make a file named `.env` and add your OpenAI key like this:
```
OPENAI_API_KEY=your_openai_key_here
```

### 4. Install Requirements
Use a virtual environment (optional but good), then run:
```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run It

Once you're set up, just run:
```bash
python main.py
```
You'll see a Google login screen — log in with the calendar account you want to use.

---

## 👥 How to Invite Someone (like your husband)

If you want every event to also go to your husband’s calendar:

1. **Open the Python file** (`main.py`)
2. Add his email like this when creating an event:
```python
"attendees": [
    {"email": "yourhusband@gmail.com"}
]
```
3. Make sure this line is also there when saving the event:
```python
service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
```
This tells Google: **“Send an invite email!”** 💌

---

## 🧹 Tip: Avoid Duplicate Events

Smartly avoids adding duplicate events by checking titles and dates

---

## ❓Need Help?

If something breaks or you get stuck:
- Check your internet connection
- Make sure your PDF is formatted correctly
- Ask your favorite tech friend 😄

Or just open an issue in this repo if using GitHub.