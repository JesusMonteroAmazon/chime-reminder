import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import re

CHIME_WEBHOOK_URL_1 = os.environ['CHIME_WEBHOOK_URL_1']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOC_ID_1 = os.environ['QUIP_DOC_ID_1']
FORCE_SEND = os.environ.get('FORCE_SEND', 'false').lower() == 'true'

def is_correct_time():
    # Get current time in UTC
    utc_now = datetime.now(pytz.UTC)
    
    # Convert to Pacific time
    pacific_tz = pytz.timezone('America/Los_Angeles')
    pacific_now = utc_now.astimezone(pacific_tz)
    
    current_hour = pacific_now.hour
    current_minute = pacific_now.minute
    
    print(f"Current Pacific time: {pacific_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Check if it's 7:00 AM or 2:00 PM Pacific
    return (current_hour == 10 and current_minute == 0) or (current_hour == 14 and current_minute == 0) or FORCE_SEND

def get_current_day():
    pacific_tz = pytz.timezone('America/Los_Angeles')
    return datetime.now(pacific_tz).strftime('%A')

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
            
def extract_content(html_content):
    print("Extracting content from HTML...")
    print(f"HTML content: {html_content[:500]}...")
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = {
        'joke': [],
        'qa_tip': [],
        'important': [],
        'metrics': [],
        'link': []
    }

    try:
        div = soup.find('div', attrs={'data-section-style': '5'})
        if div:
            main_ul = div.find('ul')
            if main_ul:
                print(f"Found main unordered list: {main_ul}")
                
                current_section = None
                for item in main_ul.find_all('li'):
                    text = item.get_text(strip=True)
                    print(f"Processing item: {text}")
                    
                    if 'joke of the day' in text.lower():
                        current_section = 'joke'
                        sections['joke'].append(text)
                    elif 'qa tip of the day' in text.lower():
                        current_section = 'qa_tip'
                    elif 'important reminder' in text.lower():
                        current_section = 'important'
                    elif 'metrics goals' in text.lower():
                        current_section = 'metrics'
                    else:
                        if current_section:
                            sections[current_section].append(text)
                            print(f"Added to {current_section} section: {text}")
                        
                    if 'remember to use the following link' in text.lower():
                        sections['link'].append(text)
                        print(f"Added to link section: {text}")
            else:
                print("No unordered list found in the div")
        else:
            print("No div with data-section-style='5' found")
    except Exception as e:
        print(f"Error while extracting content: {str(e)}")

    print("Final sections content:")
    for section, items in sections.items():
        print(f"{section}: {items}")
    return sections

def format_message(sections, current_day):
    print("Formatting message...")
    message = "🔔 **Daily Team Reminder**\n\n"

    # Joke Section
    if sections['joke']:
        message += "😄 **Joke of the Day**\n"
        for item in sections['joke']:
            if ':' in item:
                _, joke = item.split(':', 1)
                message += f"• {joke.strip()}\n"
        message += "\n"

    # QA Tip Section
    if sections['qa_tip']:
        message += "💡 **QA Tip of the Day**\n"
        for item in sections['qa_tip']:
            day_match = re.match(r'\((Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\)', item)
            if day_match:
                day = day_match.group(1)
                if day == current_day:
                    message += f"• {item.strip()}\n"
            else:
                message += f"• {item.strip()}\n"
        message += "\n"

    # Important Reminder Section
    if sections['important']:
        message += "⚠️ **Important Reminder**\n"
        for item in sections['important']:
            message += f"• {item.strip()}\n"
        message += "\n"

    # Metrics Section
    if sections['metrics']:
        message += "📊 **Metrics Goals**\n"
        for item in sections['metrics']:
            if 'remember to use the following link' not in item.lower():  # Skip the link in this section
                if ':' in item:
                    key, value = item.split(':', 1)
                    message += f"• *{key.strip()}*: {value.strip()}\n"
                else:
                    message += f"• {item.strip()}\n"
        message += "\n"

    # Link Section
    if sections['link']:
        for item in sections['link']:
            if ':' in item:
                _, value = item.split(':', 1)
                message += f"🔗 {value.strip()}\n\n"

    # Add footer
    message += "-------------------\n"
    message += "Have a great day! 🌟"

    print(f"Formatted message:\n{message}")
    return message.strip()

def send_reminder():
    try:
        # Get current time in UTC
        utc_now = datetime.now(pytz.UTC)
        
        # Convert to Pacific time
        pacific_tz = pytz.timezone('America/Los_Angeles')
        pacific_now = utc_now.astimezone(pacific_tz)
        
        # Only proceed if it's the correct time or FORCE_SEND is True
        if not is_correct_time():
            prinrint(f"Current time {pacific_now.strftime('%H:%M')} is not a scheduled reminder time. Skipping.")
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
        
        if not any(sections.values()):
            print(f"{pacific_now}: No content found in the document")
            return
            
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

if __name__ == "__main__":
    send_reminder()
