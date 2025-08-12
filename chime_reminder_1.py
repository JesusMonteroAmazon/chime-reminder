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
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific_tz)
    
    send_times = [
        (5, 0),   # 5:00 AM for Morning Sweep
        (11, 0),  # 11:00 AM for Afternoon Sweep
        (17, 0)   # 5:00 PM for Evening Sweep
    ]
    
    print(f"Current Pacific time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    last_run = get_last_run_time()
    
    for send_hour, send_minute in send_times:
        if current_time.hour == send_hour and current_time.minute == send_minute:
            if last_run is not None:
                last_run = last_run.astimezone(pacific_tz)
                if (last_run.date() == current_time.date() and 
                    last_run.hour == send_hour and
                    last_run.minute == send_minute):
                    print(f"Message already sent for {send_hour}:{send_minute:02d}. Skipping.")
                    return False
            
            save_last_run_time(current_time)
            return True
    
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
            'pending': '5',
            'distribution': {},
            'priority': 'By Timezone EST'
        }
    }

    try:
        # Extract on-call specialists from the schedule table
        data['tasks_on_call']['specialists'] = extract_specialists_from_table(soup)
        
        # Extract distribution from the schedule table
        data['tasks_on_call']['distribution'] = extract_distribution_from_table(soup)

    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    return data

def extract_specialists_from_table(soup):
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific_tz)
    current_day = current_time.strftime('%A')
    
    if current_time.hour < 12:
        table_title = "Morning Sweep (Until 12 noon)"
    elif current_time.hour < 17:
        table_title = "Afternoon Sweep (Until 5:00 pm)"
    else:
        table_title = "Evening Sweep (From 5:00 pm until calling hours)"
    
    table = soup.find('table', string=re.compile(table_title))
    if not table:
        return "No specialists found"
    
    day_index = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index(current_day)
    specialists = []
    
    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all('td')
        if len(cells) > day_index:
            specialist = cells[day_index].get_text(strip=True)
            if specialist:
                specialists.append(specialist)
    
    return ', '.join(specialists)

def extract_distribution_from_table(soup):
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific_tz)
    current_day = current_time.strftime('%A')
    
    if current_time.hour < 12:
        table_title = "Morning Sweep (Until 12 noon)"
    elif current_time.hour < 17:
        table_title = "Afternoon Sweep (Until 5:00 pm)"
    else:
        table_title = "Evening Sweep (From 5:00 pm until calling hours)"
    
    table = soup.find('table', string=re.compile(table_title))
    if not table:
        return {}
    
    day_index = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index(current_day)
    distribution = {}
    
    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all('td')
        if len(cells) > day_index:
            specialist = cells[day_index].get_text(strip=True)
            if specialist:
                if '(CAPTAIN)' in specialist.upper():
                    distribution['Captain'] = distribution.get('Captain', 0) + 1
                else:
                    distribution['Regular'] = distribution.get('Regular', 0) + 1
    
    return distribution

def format_message(data):
    message = "🔔 **Follow Up Reminders**\n\n"
    
    message += "📋 **Tasks On-Call**\n"
    if data['tasks_on_call']['specialists']:
        message += f"👥 *On-call Specialists:* {data['tasks_on_call']['specialists']}\n"
    if data['tasks_on_call']['pending']:
        message += f"📝 *Tasks pending:* {data['tasks_on_call']['pending']}\n"
    if data['tasks_on_call']['distribution']:
        message += "📊 *Distribution:*\n"
        for role, count in data['tasks_on_call']['distribution'].items():
            message += f"  • {role}: {count}\n"
    if data['tasks_on_call']['priority']:
        message += f"⚡ *Priority:* {data['tasks_on_call']['priority']}\n"
    
    message += "\n• Please follow the Tasks schedule wiki for guidance: https://w.amazon.com/bin/view/LMRCRH\n"
    message += "• Make sure you review the Taskee Dashboard (https://tiny.amazon.com/7zjRotob/TaskeeDashboard)\n"

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
        
        message = format_message(sections)  # Remove current_day parameter
        
        print("Sending message to Chime...")
        payload = {
            "Content": message
        }

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
