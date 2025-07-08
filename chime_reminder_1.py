import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import pytz
import re

CHIME_WEBHOOK_URL_1 = os.environ['CHIME_WEBHOOK_URL_1']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOCUMENT_ID_1 = os.environ['QUIP_DOCUMENT_ID_1']

def get_last_run_time():
    try:
        with open('last_run.txt', 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except:
        return None

def save_last_run_time(dt):
    with open('last_run.txt', 'w') as f:
        f.write(dt.isoformat())

def is_correct_time():
    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific_tz)
    
    # Define the times to send the reminders (10:00 AM and 2:00 PM Pacific)
    send_times = [
        (10, 0),  # 10:00 AM hour range
        (14, 0)   # 2:00 PM hour range
    ]
    
    current_hour = current_time.hour
    
    print(f"Current Pacific time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Get last run time
    last_run = get_last_run_time()
    
    # Check if current hour matches any of the send times
    for send_hour, _ in send_times:
        if current_hour == send_hour:
            # If we have a last run time, check if it was in the same hour of the same day
            if last_run is not None:
                last_run = last_run.astimezone(pacific_tz)
                if (last_run.date() == current_time.date() and 
                    last_run.hour == current_hour):
                    print(f"Message already sent for {current_hour}:00. Skipping.")
                    return False
            
            # If we get here, we should send the message
            save_last_run_time(current_time)
            return True
    
    # Also return True if FORCE_SEND is true
    if os.environ.get('FORCE_SEND', 'false').lower() == 'true':
        save_last_run_time(current_time)
        return True
    
    print(f"Current time {current_time.strftime('%H:%M')} is not a scheduled reminder time. Skipping.")
    return False

def get_current_day():
    pacific_tz = pytz.timezone('America/Los_Angeles')
    return datetime.now(pacific_tz).strftime('%A')

def extract_content(html_content):
    print("\n=== Starting content extraction ===")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    data = {
        'title': 'Follow Up reminders',
        'tasks_on_call': {
            'specialists': '',
            'pending': '',
            'distribution': '',
            'priority': ''
        }
    }

    try:
        # Find all list items
        items = soup.find_all('li')
        for item in items:
            text = item.get_text(strip=True)
            print(f"Processing item: {text}")
            
            if 'Specialists on-call:' in text:
                data['tasks_on_call']['specialists'] = text.split(':', 1)[1].strip()
            elif 'Tasks pending:' in text:
                data['tasks_on_call']['pending'] = text.split(':', 1)[1].strip()
            elif 'Distribution:' in text:
                data['tasks_on_call']['distribution'] = text.split(':', 1)[1].strip()
            elif 'Priority:' in text:
                data['tasks_on_call']['priority'] = text.split(':', 1)[1].strip()

    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    return data

def format_message(data):
    message = "🔔 **Follow Up Reminders**\n\n"
    
    message += "📋 **Tasks On-Call**\n"
    if data['tasks_on_call']['specialists']:
        message += f"👥 *Specialists on-call:* {data['tasks_on_call']['specialists']}\n"
    if data['tasks_on_call']['pending']:
        message += f"📝 *Tasks pending:* {data['tasks_on_call']['pending']}\n"
    if data['tasks_on_call']['distribution']:
        message += f"📊 *Distribution:* {data['tasks_on_call']['distribution']}\n"
    if data['tasks_on_call']['priority']:
        message += f"⚡ *Priority:* {data['tasks_on_call']['priority']}\n"

    message += "\n-------------------\n"
    message += "Have a great day! 🌟"

    print(f"\nFormatted message:\n{message}")
    return message.strip()

def send_reminder():
    try:
        # Get current time in Pacific timezone
        pacific_tz = pytz.timezone('America/Los_Angeles')
        pacific_now = datetime.now(pacific_tz)
        
        # Only proceed if it's the correct time or FORCE_SEND is True
        if not is_correct_time():
            print(f"Current time {pacific_now.strftime('%H:%M')} is not a scheduled reminder time. Skipping.")
            return
        
        print(f"\n=== Starting reminder process at {pacific_now} ===")
        
        current_day = get_current_day()
        print(f"Current day: {current_day}")
        
        print(f"CHIME_WEBHOOK_URL_1 length: {len(CHIME_WEBHOOK_URL_1)}")
        print(f"QUIP_API_TOKEN length: {len(QUIP_API_TOKEN)}")
        print(f"QUIP_DOCUMENT_ID_1: {QUIP_DOCUMENT_ID_1}")

        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOCUMENT_ID_1)
        content = thread['html']
        
        sections = extract_content(content)
        
        message = format_message(sections, current_day)
        
        print("Sending message to Chime...")
        payload = {
            "Content": message
        }

        thread = quip_client.get_thread(QUIP_DOCUMENT_ID_1)
        content = thread['html']
        print("\nHTML Content from Quip:")
        print("=" * 50)
        print(content[:1000])  # Print first 1000 characters
        print("=" * 50)

        print(f"Sending payload: {payload}")
        response = requests.post(CHIME_WEBHOOK_URL_1, json=payload)
        print(f"Chime API Response Status: {response.status_code}")
        print(f"Chime API Response Content: {response.text}")
        
        if response.status_code == 200:
            print(f"{pacific_now}: Reminder sent successfully")
        else:
            print(f"{pacific_now}: Failed to send reminder. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"{pacific_now}: Error occurred: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

class SimpleQuipClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://platform.quip-amazon.com/1"

    def get_thread(self, thread_id):
        url = f"{self.base_url}/threads/{thread_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        print(f"Fetching Quip document with URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"Quip API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            json_response = response.json()
            print(f"JSON response keys: {json_response.keys()}")
            if 'html' not in json_response:
                print("HTML not in JSON response, trying to get it from 'thread'")
                json_response['html'] = json_response['thread'].get('html', '')
            print(f"HTML content length: {len(json_response['html'])}")
            return json_response
        else:
            print(f"Error response content: {response.text}")
            response.raise_for_status()

if __name__ == "__main__":
    send_reminder()
