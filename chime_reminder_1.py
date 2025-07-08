import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

CHIME_WEBHOOK_URL = os.environ['CHIME_WEBHOOK_URL_1']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOC_ID = os.environ['QUIP_DOCUMENT_ID_1']

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
        
        print(f"\n=== Starting reminder process at {pacific_now} ===")
        
        print(f"CHIME_WEBHOOK_URL length: {len(CHIME_WEBHOOK_URL)}")
        print(f"QUIP_API_TOKEN length: {len(QUIP_API_TOKEN)}")
        print(f"QUIP_DOC_ID: {QUIP_DOC_ID}")

        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID)
        content = thread['html']
        
        data = extract_content(content)
        message = format_message(data)
        
        print("Sending message to Chime...")
        payload = {
            "Content": message
        }

        print(f"Sending payload: {payload}")
        response = requests.post(CHIME_WEBHOOK_URL, json=payload)
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

