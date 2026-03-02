import requests

backend_url = "http://localhost:4003"  # Local URL
# backend_url = "http://vcm-52527.vm.duke.edu:4003" # dev server VM URL
payload = {
    "file_content": open("data/sample_bad_idioms.py", encoding="utf-8").read(),
    "file_name": "data/sample_bad_idioms.py",
    "agent": "IDIOMS",
}

r = requests.post(f"{backend_url}/agents/IDIOMS/scan", json=payload, timeout=60)
r.raise_for_status()
data = r.json()
print("issues:", len(data["issues"]))
