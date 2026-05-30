import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Call our own local Flask server's stream proxy with OPTIONS method
local_proxy_url = "http://127.0.0.1:5000/api/stream"

print(f"Calling LOCAL HLS proxy with OPTIONS method: {local_proxy_url}\n")
try:
    r = requests.options(local_proxy_url, timeout=10)
    print("Status Code:", r.status_code)
    print("CORS Access-Control-Allow-Origin:", r.headers.get('Access-Control-Allow-Origin'))
    print("CORS Access-Control-Allow-Headers:", r.headers.get('Access-Control-Allow-Headers'))
    print("CORS Access-Control-Allow-Methods:", r.headers.get('Access-Control-Allow-Methods'))
except Exception as e:
    print("Error calling proxy with OPTIONS:", e)
