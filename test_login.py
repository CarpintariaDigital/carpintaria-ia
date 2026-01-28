import requests

url = "http://localhost:8000/api/auth/login"
headers = {"Content-Type": "application/json"}

# Test 1: Only password (new logic)
data1 = {"password": "admin"}
try:
    r1 = requests.post(url, json=data1)
    print(f"Test 1 (Password 'admin'): {r1.status_code} - {r1.text}")
except Exception as e:
    print(f"Test 1 Error: {e}")

# Test 2: Username + Password (old logic)
data2 = {"username": "admin", "password": "admin"}
try:
    r2 = requests.post(url, json=data2)
    print(f"Test 2 (User+Pass 'admin'): {r2.status_code} - {r2.text}")
except Exception as e:
    print(f"Test 2 Error: {e}")

# Test 3: Password 'carpintaria2026'
data3 = {"password": "carpintaria2026"}
try:
    r3 = requests.post(url, json=data3)
    print(f"Test 3 (Password 'carpintaria2026'): {r3.status_code} - {r3.text}")
except Exception as e:
    print(f"Test 3 Error: {e}")
