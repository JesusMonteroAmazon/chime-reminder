import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

CHIME_WEBHOOK_URL = os.environ['https://hooks.chime.aws/incomingwebhooks/c9665ec1-b8b2-4187-8458-eb9d3c9df3cd?token=ZkR6WUc3ODV8MXxQdVlFOEdjMFBKN0pPUVc0Sk16SmstRVFFRlRFZHFJN1hIVDd3ckR3a1JV']
QUIP_API_TOKEN = os.environ['WllKOU1BeHkyN24=|1782847440|pCe9fV0OlHS1mc7eiciVoGlQx9AirDs6aVj18Tia5ZY=']
QUIP_DOC_ID = os.environ['4m1YADb9L7YG']

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
    list_items = soup.find_all('li')
    if lislist_items:
        return [item.get_text(strip=True) for it item in list_items]
    paragraphs = soup.find_all('p')
    if paragraphs:
        return [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    return [soup.get_text(strip=True)]

def send_reminder():
    try:
        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID)
        content = thread['html']
        
        reminders = extract_content(content)
        
        if not reminders:
            print(f"{datetime.now()}: No content found in the document")
            return
            
        message = "🔔 Scheduled Reminder:\n" + "\n".join(f"• {reminder}" for reminder in reminders if reminder.lower() != "chime reminders")
        
        payload = {
            "Content": message
        }
        
           response = requests.post(CHIME_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print(f"{datetime.now()}: Reminder sent successfully")
        else:
            print(f"{datetime.now()}: Failed to send reminder. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"{datetime.now()}: Error occurred: {str(e)}")

if __name__ == "__main__":
    send_reminder()
