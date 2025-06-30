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
    sections = {
        'joke': [],
        'qa_tip': [],
        'important': [],
        'metrics': []
    }

    # Find the main unordered list
    main_ul = soup.find('ul')
    if main_ul:
        for li in main_ul.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            print(f"Processing list item: {text}")
            if 'joke of the day' in text.lower():
                sections['joke'].append(text)
                print(f"Added to joke section: {text}")
            elif 'qa tip of the day' in text.lower():
                nested_ul = li.find('ul')
                if nested_ul:
                    nested_items = [item.get_text(strip=True) for item in nested_ul.find_all('li')]
                    sections['qa_tip'].extend(nested_items)
                    print(f"Added to qa_tip section (nested): {nested_items}")
                else:
                    sections['qa_tip'].append(text)
                    print(f"Added to qa_tip section: {text}")
            elif 'important reminder' in text.lower():
                nested_ul = li.find('ul')
                if nested_ul:
                    nested_items = [item.get_text(strip=True) for item in nested_ul.find_all('li')]
                    sections['important'].extend(nested_items)
                    print(f"Added to important section (nested): {nested_items}")
                else:
                    sections['important'].append(text)
                    print(f"Added to important section: {text}")
            elif 'metrics goals' in text.lower():
                nested_ul = li.find('ul')
                if nested_ul:
                    nested_items = [item.get_text(strip=True) for item in nested_ul.find_all('li')]
                    sections['metrics'].extend(nested_items)
                    print(f"Added to metrics section (nested): {nested_items}")
                else:
                    sections['metrics'].append(text)
                    print(f"Added to metrics section: {text}")
    else:
        print("No main unordered list found in the HTML content")

    print(f"Extracted sections: {sections}")
    return sections

def format_message(sections):
    print("Formatmatting message...")
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
            if not item.lower().startswith('qa tip of the day'):
                message += f"• {item}\n"
        message += "\n"

    # Important Reminder Section
    if sections['important']:
        message += "⚠️ **Important Reminder**\n"
        for item in sections['important']:
            if not item.lower().startswith('important reminder'):
                message += f"• {item}\n"
        message += "\n"

    # Metrics Section
    if sections['metrics']:
        message += "📊 **Metrics Goals**\n"
        for item in sections['metrics']:
            if ':' in item:
                key, value = item.split(':', 1)
                if 'remember' in key.lower():
                    message += f"🔗 *{key.strip()}*: {value.strip()}\n"
                else:
                    message += f"• *{key.strip()}*: {value.strip()}\n"
            else:
                message += f"• {item}\n"
        message += "\n"

    # Add footer
    message += "-------------------\n"
    message += "Have a great day! 🌟"

    print(f"Formatted message:\n{message}")
    return message.strip()

def send_reminder():
    try:
        print(f"\n=== Starting reminder process at {datetime.now()} ===")
        
        print(f"CHIME_WEBHOOK_URL length: {len(CHIME_WEBHOOK_URL)}")
        print(f"QUIP_API_TOKEN length: {len(QUIP_API_TOKEN)}")
        print(f"QUIP_DOC_ID: {QUIP_DOC_ID}")

        quip_client = SimpleQuipClient(QUIP_API_TOKEN)
        thread = quip_client.get_thread(QUIP_DOC_ID)
        content = thread['html']
        
        sections = extract_content(content)
        
        if not any(sections.values()):
            print(f"{datetime.now()}: No content found in the document")
            return
            
        message = format_message(sections)
        
        print("Sending message to Chime...")
        payload = {
            "Content": message
        }
        
        print(f"Sending payload: {payload}")
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
