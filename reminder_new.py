import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

CHIME_WEBHOOK_URL = os.environ['CHIME_WEBHOOK_URL']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOC_ID = os.environ['QUIP_DOC_ID']

def get_quip_content():
    url = f"https://platform.quip-amazon.com/1/threads/{QUIP_DOC_ID}"
    headers = {
        "Authorization": f"Bearer {QUIP_API_TOKEN}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def parse_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    reminders = []
    
    # Get all list items
    for item in soup.find_all('li'):
        text = item.get_text(strip=True)
        if text and text.lower() != "chime reminders":
            reminders.append(text)
    
    return reminders

def send_reminder():
    try:
        # Get content from Quip
        quip_data = get_quip_content()
        content = quip_data['html']
        
        # Parse reminders
        reminders = parse_content(content)
        
        if not reminders:
            print(f"{datetime.now()}: No reminders found")
            return
            
        # Prepare message
        message = "🔔 Scheduled Reminder:\n" + "\n".join(f"• {reminder}" for reminder in reminders)
        
        # Send to Chime
        response = requests.post(
            CHIME_WEBHOOK_URL, 
            json={"Content": message}
        )
        
        if response.status_code == 200:
            print(f"{da{datetime.now()}: Reminder sent successfully")
        else:
            print(f"{datetime.now()}: Failed to send reminder. Status: {response.status_code}")
            
    except Exception as e:
        print(f"{datetime.now()}: Error occurred: {str(e)}")

if __name__ == "__main__":
    send_reminder()
