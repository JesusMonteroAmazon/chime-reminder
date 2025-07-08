import requests
import json
from quip_api import QuipClient

# Quip API setup
QUIP_ACCESS_TOKEN = 'WllKOU1BQnN1U2I=|1783538343|p9s1+4ghw9RpgIlqmK3Vfsu0pbuKC9zxYOEY1Y999kk='
quip_client = QuipClient(access_token=QUIP_ACCESS_TOKEN)

# Chime webhook URL
CHIME_WEBHOOK_URL_1 = 'https://hooks.chime.aws/incomingwebhooks/acb671ac-6d0a-4dd9-ab85-5af4592fb29d?token=emN5RkxlR3Z8MXwtNkd1LWdDTDJ2T09ybGw5dW9UT0NwVFFKU2JkV2lOR3VpWVV1VTNMVi1N'

def get_quip_data(document_id):
    # Fetch the document content
    document = quip_client.get_thread(document_id)
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

    response = requests.post(CHIME_WEBWEBHOOK_URL_1, data=json.dumps(payload))
    if response.status_code != 200:
        raise ValueError(f'Request to Chime returned an error {response.status_code}, the response is:\n{response.text}')

def main():
    document_id = 'aeiqAWxRHTsm'
    data = get_quip_data(document_id)
    send_to_chime(data)

if __name__ == '__main__':
    main()
