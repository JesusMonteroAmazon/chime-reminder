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
        print(f"Fetching Quip document with URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"Quip API Response Status: {response.status_code}")
        response.raise_for_status()
        return response.json()

def extract_content(html_content):
    print("Extracting content from HTML...")
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = {}
    current_section = None

    # Print the raw HTML content for debugging
    print(f"Raw HTML content: {html_content[:500]}...") # First 500 characters

    for element in soup.find_all(['h1', 'h2', 'h3', 'li']):
        if element.name in ['h1', 'h2', 'h3']:
            current_section = element.text.strip()
            sections[current_section] = []
            print(f"Found section: {current_section}")
        elif element.name == 'li' and current_section:
            item_text = element.text.strip()
            sections[current_section].append(item_text)
            print(f"Added item to {current_section}: {item_text}")

    return sections

def format_message(sections):
    print("Formatting message...")
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

    print(f"Formatted message:\n{message}")
    return message.strip()

def send_reminder():
    try:
        print(f"\n=== Starting reminder process at {datetime.now()} ===")
        
        # Print environment variables (masked)
        print(f"CHIME_WEBHOOK_URL: {'*' * len(CHIME_WEBHOOK_URL)}")
        print(f"QUIP_API_TOKEN: {'*' * len(QUIP_API_TOKEN)}")
        print(f"QUIP_DOC_ID: {QUIP_DOC_ID}")

        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID)
        content = thread['html']
        
        sections = extract_contontent(content)
        
        if not sections:
            print(f"{datetime.now()}: No content found in the document")
            return
            
        message = format_message(sections)
        
        print("Sending message to Chime...")
        payload = {
            "Content": message
        }
        
        response = requests.post(CHIME_WEBHOOK_URL, json=payload)
        print(f"Chime API Response Status: {response.status_code}")
        print(f"Chime API Response Content: {response.text}")
        
        if response.status_code == 200:
            print(f"{datetime.now()}: Reminder sent successfully")
        else:
            print(f"{datetime.now()}: Failed to send reminder. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"{datetime.now()}: Error occurred: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    send_reminder()
