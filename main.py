import os
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
import httpx

# Import from our fresh modular files
from config import settings
from models import IncomingRequest, APIResponse, ExtractedIntelligence
from logger import HoneypotLogger

# Initialize FastAPI app
app = FastAPI(title="Agentic Honeypot Core", version="2.0.0")

# Initialize our async modules
logger = HoneypotLogger()
ai_client = AsyncOpenAI(
    base_url=settings.AI_BASE_URL,
    api_key=settings.AI_API_KEY
)

# In-memory session tracking store
sessions = {}

# =============================================================================
# HELPER FUNCTIONS & MIDDLEWARE
# =============================================================================
def validate_api_key(x_api_key: str):
    """Strictly validates inbound API token header."""
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_or_create_session(session_id: str) -> dict:
    """Tracks state memory safely across conversational turns."""
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": datetime.now(timezone.utc),
            "conversation": [],
            "extracted_intel": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": [],
            },
            "scam_detected": False,
            "agent_notes": "",
            "callback_sent": False,
        }
    return sessions[session_id]

def should_trigger_callback(session: dict) -> bool:
    """Evaluates metrics to determine if engagement lifecycle is complete."""
    if session["callback_sent"] or not session["scam_detected"]:
        return False

    total_msgs = len(session["conversation"])
    has_intel = any(len(v) > 0 for v in session["extracted_intel"].values() if isinstance(v, list))

    return (total_msgs >= 5 and has_intel) or total_msgs >= 10

# =============================================================================
# ASYNCHRONOUS ENGINE LIFECYCLE OPERATIONS
# =============================================================================
async def detect_scam_intent(text: str) -> tuple[bool, str]:
    """Queries Groq asynchronously to evaluate text for scam classification."""
    try:
        response = await ai_client.chat.completions.create(
            model=settings.AI_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a fraud detection expert. Analyze the message and determine if it contains scam intent. Reply with ONLY 'SCAM' or 'NOT_SCAM' followed by a brief reason.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=100,
        )
        # Safe Extraction: Fallback to empty string if content is None
        raw_content = response.choices[0].message.content
        if not raw_content:
            return False, "Analysis failed: Empty or null response from LLM engine."
            
        result = raw_content.strip()

        if "NOT_SCAM" in result.upper():
            return False, result.replace("NOT_SCAM", "").strip(" :\n-")
        elif "SCAM" in result.upper():
            return True, result.replace("SCAM", "").strip(" :\n-")
        return False, "Analysis complete"
    except Exception as e:
        await logger.log_event("SYSTEM", "llm_error", {"error": str(e), "stage": "intent_detection"})
        return False, f"Detection failed: {str(e)}"

async def extract_intelligence(scammer_text: str, existing_intel: dict) -> dict:
    """Uses LLM JSON mode asynchronously to map elements safely out of text."""
    try:
        response = await ai_client.chat.completions.create(
            model=settings.AI_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract scam intelligence from the text.\n"
                        "Return ONLY valid JSON.\n"
                        "All keys must exist and each value must be an array of strings (use [] if none):\n"
                        "bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords."
                    ),
                },
                {"role": "user", "content": scammer_text},
            ],
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        intel = json.loads(raw)

        # Merge loops cleanly
        for key in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"]:
            existing_intel.setdefault(key, [])
            for item in intel.get(key, []) or []:
                if isinstance(item, str) and item and item not in existing_intel[key]:
                    existing_intel[key].append(item)
        return existing_intel
    except Exception as e:
        await logger.log_event("SYSTEM", "llm_error", {"error": str(e), "stage": "intel_extraction"})
        return existing_intel

from typing import List, Literal, cast, Any
from openai.types.chat import ChatCompletionMessageParam

async def generate_agent_reply(latest_scammer_message: str, conversation_history: List[dict[str, Any]]) -> str:
    """Synthesizes human response context natively without thread locking."""
    # 1. Explicitly type the list using OpenAI's message parameter types
    messages: List[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are a victim receiving a scam message. Respond naturally (confused, concerned) "
                "to keep the scammer talking. NEVER reveal that you know it's a scam. Ask clarifying "
                "questions that make them reveal more details (bank, link, phone, UPI ID). Max 1-3 sentences."
            ),
        }
    ]
    role_map = {"scammer": "user", "user": "assistant"}

    # 2. Iterate through history using standard dict lookups safely
    for msg in conversation_history[-5:]:
        sender_value = str(msg.get("sender", "scammer"))
        resolved_role = cast(Literal["user", "assistant", "system"], role_map.get(sender_value, "user"))
        
        history_message = cast(ChatCompletionMessageParam, {
            "role": resolved_role, 
            "content": str(msg.get("text", ""))
        })
        messages.append(history_message)

    # 3. Cast the trailing dynamic user message payload dictionary explicitly
    user_message = cast(ChatCompletionMessageParam, {
        "role": "user", 
        "content": latest_scammer_message
    })
    messages.append(user_message)

    try:
        response = await ai_client.chat.completions.create(
            model=settings.AI_MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
        )
        
        raw_content = response.choices[0].message.content
        if not raw_content:
            return "I'm a bit confused. Can you please explain what you mean by that?"
            
        return raw_content.strip()
        
    except Exception as e:
        await logger.log_event("SYSTEM", "llm_reply_error", {"error": str(e)})
        return "I don't understand what's happening. Can you please clarify what I need to do?"



# =============================================================================
# EXPOSED CORE ROUTE ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/honeypot")
async def honeypot_endpoint(
    request: IncomingRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None),
):
    # 1. Authenticate Request
    validate_api_key(x_api_key)

    # 2. Track Session
    session = get_or_create_session(request.sessionId)
    incoming_text = request.message.text

    # Log inbound transaction into JSONL
    await logger.log_event(request.sessionId, "message_received", {"sender": "scammer", "text": incoming_text})

    session["conversation"].append({
        "sender": "scammer",
        "text": incoming_text,
        "timestamp": request.message.timestamp or datetime.now(timezone.utc).isoformat()
    })

    # 3. Dynamic Scam Intent Filtering
    if not session["scam_detected"]:
        is_scam, reason = await detect_scam_intent(incoming_text)
        session["scam_detected"] = is_scam
        session["agent_notes"] = reason
        await logger.log_event(request.sessionId, "intent_evaluated", {"is_scam": is_scam, "reason": reason})

    # Standard safe response strategy if flagged as non-threat
    if not session["scam_detected"]:
        return JSONResponse({"status": "success", "reply": "Hello! How can I help you today?"})

    # 4. Extract Intel and Synthesize Counter-Measures
    session["extracted_intel"] = await extract_intelligence(incoming_text, session["extracted_intel"])
    await logger.log_event(request.sessionId, "intelligence_updated", {"intel_snapshot": session["extracted_intel"]})

    agent_reply_text = await generate_agent_reply(incoming_text, session["conversation"])

    session["conversation"].append({
        "sender": "user",
        "text": agent_reply_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Log outbound response action into JSONL
    await logger.log_event(request.sessionId, "agent_reply_dispatched", {"sender": "user", "text": agent_reply_text})


    return JSONResponse({"status": "success", "reply": agent_reply_text})