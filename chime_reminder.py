import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

CHIME_WEBHOOK_URL = os.environ['CHIME_WEBHOOK_URL']
QUIP_API_TOKEN = os.environ['QUIP_API_TOKEN']
QUIP_DOC_ID = os.environ['QUIP_DOC_ID']

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
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def extract_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = {}
    current_section = None

    for element in soup.find_all(['h1', 'h2', 'h3', 'li']):
        if element.name in ['h1', 'h2', 'h3']:
            current_section = element.text.strip()
            sections[current_section] = []
        elif element.name == 'li' and current_section:
            sections[current_section].append(element.text.strip())

    return sections

def format_message(sections):
    message = "🔔 **Daily Reminder**\n\n"

    for section, items in sections.items():
        if section.lower() == "this is the reminder":
            continue
        message += f"**{section}**\n"
        for item in items:
            if ":" in item:
                key, value = item.split(":", 1)
                message += f"• *{key.strip()}*: {value.strip()}\n"
            else:
                message += f"• {item}\n"
        message += "\n"

    return message.strip()

def send_reminder():
    try:
        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID)
        content = thread['html']
        
        sections = extract_content(content)
        
        if not sections:
            print(f"{datetime.now()}: No content found in the document")
            return
            
        message = format_message(sections)
        
        paylayload = {
            "Content": message
        }
        
        response = requests.post(CHIME_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print(f"{datetime.now()}: Reminder sent successfully")
            print(f"Message content:\n{message}")
        else:
            print(f"{datetime.now()}: Failed to send reminder. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"{datetime.now()}: Error occurred: {str(e)}")

if __name__ == "__main__":
    send_reminder()
