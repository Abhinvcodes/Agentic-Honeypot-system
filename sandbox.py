import asyncio
import httpx
import sys
from datetime import datetime

TARGET_URL = "http://localhost:8000/api/honeypot"
API_KEY = "test-key-12345"
# This guarantees the server builds a completely clean profile every time you launch it.
# FIX: Generates a clean, readable timestamp format (e.g., 2026-05-23_13-45-12)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_ID = f"interactive-sandbox-session-{timestamp}"

async def async_input(prompt: str) -> str:
    """
    Runs the standard blocking input function inside a separate thread 
    so it doesn't freeze or crash the asyncio event loop.
    """
    # Runs the synchronous input() function in the default executor thread pool
    return await asyncio.to_thread(input, prompt)

async def start_interactive_session():
    conversation_history = []
    
    print("====================================================")
    print("      AGENTIC HONEYPOT INTERACTIVE SANDBOX          ")
    print("====================================================")
    print(f"Session ID: {SESSION_ID}")
    print("Type 'exit' or 'quit' at any time to end the session.\n")
    
    async with httpx.AsyncClient(http2=True) as client:
        while True:
            # 1. Use our new non-blocking async input helper
            try:
                scammer_text = await async_input("😈 You (Scammer) > ")
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Exiting sandbox.")
                break
                
            if scammer_text.strip().lower() in ['exit', 'quit']:
                print("👋 Session ended.")
                break
                
            if not scammer_text.strip():
                continue

            # 2. Package the payload to hit your FastAPI application
            payload = {
                "sessionId": SESSION_ID,
                "message": {
                    "sender": "scammer",
                    "text": scammer_text
                },
                "conversationHistory": conversation_history,
                "metadata": {
                    "channel": "Live Terminal",
                    "language": "English",
                    "locale": "Global"
                }
            }
            
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            }
            
            # 3. Transmit to local server
            try:
                print("⏳ Agent thinking...", end="", flush=True)
                response = await client.post(TARGET_URL, json=payload, headers=headers, timeout=30.0)
                
                # Erase the "Agent thinking..." line completely
                print("\r\033[K", end="", flush=True)
                
                if response.status_code == 200:
                    data = response.json()
                    agent_reply = data.get("reply", "")
                    
                    # 4. Print the AI's natural response
                    print(f"🤖 Agent Reply   > {agent_reply}\n")
                    
                    # Keep local history state matching what the endpoint expects
                    conversation_history.append({"sender": "scammer", "text": scammer_text})
                    conversation_history.append({"sender": "user", "text": agent_reply})
                else:
                    print(f"❌ Server Error ({response.status_code}): {response.text}\n")
                    
            except Exception as e:
                print(f"\r❌ Network loop failed: {str(e)}\n")

if __name__ == "__main__":
    try:
        asyncio.run(start_interactive_session())
    except KeyboardInterrupt:
        print("\n👋 Sandbox terminated.")