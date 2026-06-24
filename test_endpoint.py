from fastapi.testclient import TestClient
from main import app
import os
import json

os.environ['CRON_SECRET_KEY'] = 'test_key'
client = TestClient(app)

print("Starting test...")
response = client.post('/api/v1/admin/trigger-sweep', headers={'X-Cron-Signature': 'test_key'})
print('Status Code:', response.status_code)
print('Response:', response.json())
