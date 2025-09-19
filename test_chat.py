import requests

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"message": "Which crop should I grow in September?"}
)
print("Status code:",response.status_code)
print("Response text:",response.text)