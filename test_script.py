import asyncio
import httpx

# Configurations matching your .env settings
TARGET_URL = "http://localhost:8000/api/honeypot"
API_KEY = "test-key-12345"
SESSION_ID = "session-test-999"

# A multi-turn scam dialog dataset simulating real scam dynamics
SIMULATED_TURNS = [
    {
        "step": 1,
        "text": "Your bank account will be blocked today. Verify immediately.",
        "sender": "scammer"
    },
    {
        "step": 2,
        "text": "Share your UPI ID scammer.support@upi to avoid account suspension.",
        "sender": "scammer"
    },
    {
        "step": 3,
        "text": "Go to https://secure-kyc-update.example/ and enter your card number now.",
        "sender": "scammer"
    }
]

async def execute_simulation():
    conversation_history = []
    
    # Initialize a non-blocking HTTPX async client connection pool
    async with httpx.AsyncClient(http2=True) as client:
        print(f"🚀 Starting Honeypot Multi-Turn Simulation for Session: {SESSION_ID}\n")
        
        for turn in SIMULATED_TURNS:
            print(f"--- [STEP {turn['step']}] Scammer Sends ---")
            print(f"💬 Text: \"{turn['text']}\"")
            
            # Construct the exact IncomingRequest Pydantic data schema payload
            payload = {
                "sessionId": SESSION_ID,
                "message": {
                    "sender": turn["sender"],
                    "text": turn["text"]
                },
                "conversationHistory": conversation_history,
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
            
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            }
            
            try:
                # Dispatch the async POST request to your API
                response = await client.post(TARGET_URL, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code == 200:
                    data = response.json()
                    agent_reply = data.get("reply", "")
                    print(f"🤖 Honeypot Agent Reply: \"{agent_reply}\"\n")
                    
                    # Update local history tracking to mimic multi-turn retention state behavior
                    conversation_history.append({"sender": "scammer", "text": turn["text"]})
                    conversation_history.append({"sender": "user", "text": agent_reply})
                else:
                    print(f"❌ Server rejected transaction. Status: {response.status_code}, Detail: {response.text}\n")
                    break
                    
            except Exception as e:
                print(f"💥 Network request failed: {str(e)}\n")
                break
                
            # Small realistic sleep delay between conversational turns
            await asyncio.sleep(1.5)

if __name__ == "__main__":
    # Standard modern entry loop execution for async Python environments
    asyncio.run(execute_simulation())