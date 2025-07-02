import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import pytz
import re

CHIME_WEBHOOK_URL_1 = os.environ['CHIME_WEBHOOK_URL_1']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOC_ID_1 = os.environ['QUIP_DOC_ID_1']

def is_correct_time():
    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pacific_tz)
    
    # Define the times to send the reminders (10:00 AM and 2:00 PM Pacific)
    send_times = [
        time(10, 0),  # 10:00 AM
        time(14, 0)   # 2:00 PM
    ]
    
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    print(f"Current Pacific time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Check if current time matches any of the send times (within a 5-minute window)
    for send_time in send_times:
        if (current_hour == send_time.hour and 
            current_minute >= send_time.minute and 
            current_minute < send_time.minute + 5):
            return True
    
    # Also return True if FORCE_SEND is true
    if os.environ.get('FORCE_SEND', 'false').lower() == 'true':
        return True
    
    return False

def get_current_day():
    pacific_tz = pytz.timezone('America/Los_Angeles')
    return datetime.now(pacific_tz).strftime('%A')

def extract_content(html_content):
    print("Extracting content from HTML...")
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = {
        'joke': {'Sunday': [], 'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': []},
        'qa_tip': {'Sunday': [], 'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': []},
        'important': {'Sunday': [], 'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': []},
        'metrics': [],
        'link': []
    }

    try:
        div = soup.find('div', attrs={'data-section-style': '5'})
        if div:
            main_ul = div.find('ul')
            if main_ul:
                current_section = None
                
                # Process main sections
                for item in main_ul.find_all('li', recursive=False):
                    text = item.get_text(strip=True)
                    print(f"Processing main item: {text}")
                    
                    if 'joke of the day' in text.lower():
                        current_section = 'joke'
                    elif 'qa tip of the day' in text.lower():
                        current_section = 'qa_tip'
                    elif 'important reminder' in text.lower():
                        current_section = 'important'
                    elif 'metrics goals' in text.lower():
                        current_section = 'metrics'
                    
                    # Process sub-items
                    if current_section in ['joke', 'qa_tip', 'important']:
                        sub_ul = item.find('ul')
                        if sub_ul:
                            for sub_item in sub_ul.find_all('li'):
                                sub_text = sub_item.get_text(strip=True)
                                print(f"Processing sub-item: {sub_text}")
                                day_match = re.match(r'\((Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\)', sub_text)
                                if day_match:
                                    day = day_match.group(1)
                                    # Remove the day prefix
                                    content = re.sub(r'\([^)]*\)\s*', '', sub_text).strip()
                                    sections[current_section][day].append(content)
                                    print(f"Added {current_section} for {day}: {content}")
                                else:
                                    print(f"No day match found for: {sub_text}")
                    elif current_section == 'metrics':
                        sections['metrics'].append(text)
                        if 'remember to use the following link' in text.lower():
                            sections['link'].append(text)
                        print(f"Added metric: {text}")
            else:
                print("No unordered list found in the div")
        else:
            print("No div with data-section-style='5' found")
    except Exception as e:
        print(f"Error while extracting content: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    print("Final sections content:")
    for section, items in sections.items():
        print(f"{section}: {items}")
    return sections

def format_message(sections, current_day):
    print(f"Formatting message for {current_day}...")
    message = "🔔 **Daily Team Reminder**\n\n"

    # Joke Section for current day
    if sections['joke'][current_day]:
        message += "😄 **Joke of the Day**\n"
        for joke in sections['joke'][current_day]:
            message += f"• {joke}\n"
        message += "\n"

    # QA Tip Section for current day
    if sections['qa_tip'][current_day]:
        message += "💡 **QA Tip of the Day**\n"
        for tip in sections['qa_tip'][current_day]:
            message += f"• {tip}\n"
        message += "\n"

    # Important Reminder Section for current day
    if sections['important'][current_day]:
        message += "⚠️ **Important Reminder**\n"
        for reminder in sections['important'][current_day]:
            message += f"• {reminder}\n"
        message += "\n"

    # Metrics Section
    if sections['metrics']:
        message += "📊 **Metrics Goals**\n"
        for metric in sections['metrics']:
            if ':' in metric:
                key, value = metric.split(':', 1)
                message += f"• *{key.strip()}*: {value.strip()}\n"
            else:
                message += f"• {metric}\n"
        message += "\n"

    # Link Section
    if sections['link']:
        for link in sections['link']:
            if ':' in link:
                _, value = link.split(':', 1)
                message += f"🔗 {value.strip()}\n"

    # Add footer
    message += "-------------------\n"
    message += "Have a great day! 🌟"

    print(f"Formatted message:\n{message}")
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
        print(f"QUIP_DOC_ID_1: {QUIP_DOC_ID_1}")

        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID_1)
        content = thread['html']
        
        sections = extract_content(content)
        
        message = format_message(sections, current_day)
        
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
