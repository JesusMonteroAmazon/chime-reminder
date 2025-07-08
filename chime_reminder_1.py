import requests
import json
import os

def print_env_vars():
    print("Environment variables:")
    print(f"QUIP_ACCESS_TOKEN: {'Set' if os.environ.get('QUIP_ACCESS_TOKEN') else 'Not set'}")
    print(f"CHIME_WEBHOOK_URL_1: {'Set' if os.environ.get('CHIME_WEBHOOK_URL_1') else 'Not set'}")
    print(f"QUIP_DOCUMENT_ID_1: {'Set' if os.environ.get('QUIP_DOCUMENT_ID_1') else 'Not set'}")

# Quip API setup
QUIP_ACCESS_TOKEN = os.environ.get('QUIP_ACCESS_TOKEN')
QUIP_API_URL = 'https://platform.quip.com/1/threads/'

# Chime webhook URL
CHIME_WEBHOOK_URL = os.environ.get('CHIME_WEBHOOK_URL_1')

def get_quip_data(document_id):
    headers = {
        'Authorization': f'Bearer {QUIP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # First, let's test the authentication
        test_response = requests.get('https://platform.quip.com/1/users/current', headers=headers)
        if test_response.status_code == 401:
            print("Authentication failed. Response:", test_response.text)
            raise ValueError("Quip API authentication failed. Please check your access token.")
        
        # If authentication is successful, proceed with the document request
        response = requests.get(f"{QUIP_API_URL}{document_id}", headers=headers)
        
        if response.status_code != 200:
            print(f"Error response from Quip API: {response.text}")
            raise ValueError(f'Request to Quip API failed with status code {response.status_code}')
        
        document = response.json()
        content = document.get('html', '')
        
        if not content:
            raise ValueError('No content received from Quip document')
        
        # Parse the HTML content
        lines = content.split('\n')
        data = {
            'title': 'Follow Up reminders',
            'tasks_on_call': {
                'title': 'Tasks on-call',
                'specialists': 'N/A',
                'pending': 'N/A',
                'distribution': 'N/A'
            },
            'priority': 'N/A'
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
        
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {str(e)(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

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

    try:
        response = requests.post(CHIME_WEBHOOK_URL, json=payload)  # Changed to json parameter
        if response.status_code != 200:
            print(f"Chime API response: {response.text}")
            raise ValueError(f'Request to Chime returned an error {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Chime: {str(e)}")
        raise

def main():
    print_env_vars()
    
    document_id = os.environ.get('QUIP_DOCUMENT_ID_1')
    if not document_id:
        raise ValueError('QUIP_DOCUMENT_ID_1 environment variable is not set')
    
    if not QUIP_ACCESS_TOKEN:
        raise ValueError('QUIP_ACCESS_TOKEN environment variable is not set')
        
    if not CHIME_WEBHOOK_URL:
        raise ValueError('CHIME_WEBHOOK_URL_1 environment variable is not set')
    
    # Print token format (first and last 4 characters)
    if len(QUIP_ACCESS_TOKEN) > 8:
        print(f"Token format: {QUIP_ACCESS_TOKEN[:4]}...{QUIP_ACCESS_TOKEN[-4:]}")
    
    data = get_quip_data(document_id)
    send_to_chime(data)

if __name__ == '__main__':
    main()

