import requests
import json
import os

# Quip API setup
QUIP_ACCESS_TOKEN = os.environ.get('QUIP_ACCESS_TOKEN')
QUIP_API_URL = 'https://platform.quip.com/1/threads/'

# Chime webhook URL
CHIME_WEBHOOK_URL_1 = os.environ.get('CHIME_WEBHOOK_URL_1')

def get_quip_data(document_id):
    headers = {
        'Authorization': f'Bearer {QUIP_ACCESS_TOKEN}'
    }
    response = requests.get(f"{QUIP_API_URL}{document_id}", headers=headers)
    if response.status_code != 200:
        raise ValueError(f'Request to Quip API failed with status code {response.status_code}')
    
    document = response.json()
    content = document['html']
    
    # Parse the HTML content (you may need to use a proper HTML parser for more complex documents)
    # This is a simplified example
    lines = content.split('\n')
    data = {
        'title': 'Follow Up reminders',
        'tasks_on_call': {},
        'priority': ''
    }
    
    for line in lines:
        if 'Tasks on-call' in line:
            data['tasks_on_call']['title'] = 'Tasks on-call'
        elif 'Specialists on-call:' in line:
            data['tasks_on_call']['specialists'] = line.split(':')[1].strip()
        elif 'Tasks pending:' in line:
            data['tasks_on_call']['pending'] = line.split(':')[1].strip()
        elif 'Distribution:' in line:
            data['tasks_on_call']['distribution'] = line.split(':')[1].strip()
        elif 'Priority:' in line:
            data['priority'] = line.split(':')[1].strip()
    
    return data

def send_to_chime(data):
    message = f"*{data['title']}*\n\n"
    message += f"*{data['tasks_on_call']['title']}*\n"
    message += f"- Specialists on-call: {data['tasks_on_call']['specialists']}\n"
    message += f"- Tasks pending: {data['tasks_on_call']['pending']}\n"
    message += f"- Distribution: {data['tasks_on_call']['distribution']}\n"
    message += f"- Priority: {data['priority']}\n"

    payload = {
        'Content': message
    }

    response = requests.post(CHIME_WEBHOOK_URL_1, data=json.dumps(payload))
    if response.status_code != 200:
        raise ValueError(f'Request to Chime returned an error {response.status_code}, the response is:\n{response.text}')

def main():
    document_id = os.environ.get('QUIP_DOCUMENT_ID_1')
    if not document_id:
        raise ValueError('QUIP_DOCUMENT_ID_1 environment variable is not set')
    data = get_quip_data(document_id)
    send_to_chime(data)

if __name__ == '__main__':
    main()
