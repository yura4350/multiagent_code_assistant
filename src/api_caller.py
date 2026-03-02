import requests

backend_url = "http://localhost:4003"  # or your VM URL
payload = {
    "file_content": open("data/sample_bad_idioms.py", encoding="utf-8").read(),
    "file_name": "data/sample_bad_idioms.py",
    "agent": "IDIOMS",
}

r = requests.post(f"{backend_url}/analyze", json=payload, timeout=60)
r.raise_for_status()
data = r.json()
print("issues:", len(data["issues"]))
print("suggestions:", len(data["suggestions"]))