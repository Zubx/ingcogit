import requests

def get_public_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        if response.status_code == 200:
            data = response.json()
            return data['ip']
        else:
            return "Unable to retrieve IP"
    except Exception as e:
        return str(e)

public_ip = get_public_ip()
print("Your public IP address is:", public_ip)
