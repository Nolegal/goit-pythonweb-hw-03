import requests


try:
    r = requests.get('http://localhost:3000/')
    print("Status code:", r.status_code)
    print("Text:", r.text)
    print("Headers:", r.headers)
except requests.exceptions.ConnectionError:
    print(f"Error: Could not connect to the server. Make sure it is running.")
