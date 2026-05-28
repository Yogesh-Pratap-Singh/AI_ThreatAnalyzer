import httpx
import sys

URL = "http://localhost:8000/api/v1"

def run_integration_tests():
    print("--- Starting Integration Verification ---")
    client = httpx.Client(headers={"Content-Type": "application/json"})
    
    # 1. Test Login
    print("\n1. Testing Login...")
    payload = {"email": "analyst@yourorg.com", "password": "Password123"}
    response = client.post(f"{URL}/auth/login", json=payload)
    print(f"Login response status: {response.status_code}")
    assert response.status_code == 200, "Login failed!"
    login_data = response.json()
    print(f"Logged in user: {login_data['user']['full_name']} ({login_data['user']['role']})")
    
    # 2. Test Get Me
    print("\n2. Testing /auth/me...")
    response = client.get(f"{URL}/auth/me")
    print(f"Get Me response status: {response.status_code}")
    assert response.status_code == 200, "Get Me failed!"
    me_data = response.json()
    print(f"Current user session verified: {me_data['email']}")
    
    # 3. Test Fetch Alerts
    print("\n3. Testing /alerts...")
    response = client.get(f"{URL}/alerts")
    print(f"Fetch alerts status: {response.status_code}")
    assert response.status_code == 200, "Alert retrieval failed!"
    alerts_data = response.json()
    alerts_list = alerts_data.get("alerts", [])
    print(f"Alerts count in queue: {len(alerts_list)}")
    for al in alerts_list:
        print(f"  - [{al['severity'].upper()}] {al['title']} | Tactic: {al['mitre_tactic']} | Status: {al['status']}")
    
    # 4. Test Fetch Reports Summary
    print("\n4. Testing /reports/summary...")
    from datetime import datetime, timedelta
    from_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
    to_time = datetime.utcnow().isoformat()
    response = client.get(f"{URL}/reports/summary", params={"from_time": from_time, "to_time": to_time})
    print(f"Fetch reports status: {response.status_code}")
    assert response.status_code == 200, "Report summary failed!"
    reports_data = response.json()
    print(f"Reports summary stats: Total Alerts: {reports_data['total_alerts']} | FP Rate: {reports_data['false_positive_rate']} | Mean Triage Time: {reports_data['mean_triage_time_minutes']} min")
    
    print("\n--- All Integration Tests Passed Successfully! ---")

if __name__ == "__main__":
    try:
        run_integration_tests()
    except AssertionError as ae:
        print(f"Assertion Error: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
