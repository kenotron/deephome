import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = f"test-session-{int(time.time())}"

def run_query(prompt, session_id):
    print(f"\n--- Sending: {prompt} (Session: {session_id}) ---")
    url = f"{BASE_URL}/agent/query"
    params = {"prompt": prompt, "session_id": session_id}
    
    response_text = ""
    with requests.get(url, params=params, stream=True) as r:
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    try:
                        data = json.loads(decoded_line[6:])
                        if data["type"] == "response":
                            print(data["payload"], end="", flush=True)
                            response_text += data["payload"]
                        elif data["type"] == "log":
                            print(f"\n[LOG] {data['payload']}")
                    except Exception as e:
                        pass
    print("\n")
    return response_text

def test_persistence():
    # Turn 1: Set context
    print("Test 1: Setting Context")
    run_query("Hello, my name is DeepHomeTester.", SESSION_ID)
    
    # Turn 2: Retrieve context
    print("Test 2: Retrieving Context")
    response = run_query("What is my name?", SESSION_ID)
    
    if "DeepHomeTester" in response:
        print("✅ SUCCESS: Context Preserved!")
    else:
        print("❌ FAILURE: Context Lost.")

if __name__ == "__main__":
    test_persistence()
