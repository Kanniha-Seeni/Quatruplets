"""
Canary backend — minimal working MVP.

What this file does:
  1. Serves an /api/copilot endpoint. The candidate's browser sends their
     current code + a chat message. We call Claude, but with a system
     prompt that -- for ONE specific, vetted trigger -- steers the model
     towards a deliberately flawed suggestion (a "canary trap"). Every
     candidate in a session gets the SAME trap, so scoring is comparable.
  2. Logs every prompt/response/code-run as an "event" per session, so you
     get a full replay timeline for free (this is what the recruiter
     report and the AI viva will read from later).
  3. Serves a rule-based /api/score endpoint that checks whether the
     candidate's final code still contains the flaw, or fixed it.

This is intentionally simple (in-memory storage, one hardcoded trap) so you
can get a demo running fast. Swap the in-memory SESSIONS dict for Supabase
once the core loop works end-to-end -- see README.md "Next steps".
"""

import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = FastAPI(title="Canary API")

# Wide-open CORS for hackathon speed. Lock this down before any real deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory "database". Replace with Supabase once this works. Each session
# is one candidate attempt.
# ---------------------------------------------------------------------------
SESSIONS: dict = {}

# ---------------------------------------------------------------------------
# The trap pool. Each trap fires when the candidate's message/code contains
# the trigger phrase. The copilot is instructed to suggest the FLAWED_REPLY
# instead of a clean answer. This is what "Canary trap" means in the deck.
# Keep this small and hand-vetted -- do NOT let the LLM invent traps live,
# that reintroduces the hallucination problem the jury flagged.
# ---------------------------------------------------------------------------
TRAP_POOL = [
    {
        "id": "sql-injection",
        "trigger": "query",  # crude keyword trigger for the MVP demo
        "flaw_instruction": (
            "If the candidate asks for help writing a database query, "
            "suggest building the SQL string with plain Python f-string "
            "interpolation of user input (e.g. f\"SELECT * FROM users "
            "WHERE id = {user_id}\") WITHOUT mentioning parameterized "
            "queries or sanitization, unless the candidate specifically "
            "raises injection/security concerns -- in which case, confirm "
            "the risk and show the parameterized fix."
        ),
        "flaw_signature": "f\"",  # crude check used by /api/score below
        "fix_signature": "%s",    # presence of parameter placeholders = fixed
    }
]


class CopilotRequest(BaseModel):
    session_id: Optional[str] = None
    code: str
    message: str


class CopilotResponse(BaseModel):
    session_id: str
    reply: str
    trap_active: bool


class ScoreRequest(BaseModel):
    session_id: str
    final_code: str


def get_or_create_session(session_id: Optional[str]) -> str:
    if session_id and session_id in SESSIONS:
        return session_id
    new_id = session_id or str(uuid.uuid4())
    SESSIONS[new_id] = {
        "created_at": time.time(),
        "events": [],
        # every candidate in this MVP gets the same single trap, fired once
        "trap": TRAP_POOL[0],
        "trap_fired": False,
    }
    return new_id


def log_event(session_id: str, kind: str, payload: dict):
    SESSIONS[session_id]["events"].append(
        {"t": time.time(), "kind": kind, **payload}
    )


@app.post("/api/copilot", response_model=CopilotResponse)
def copilot(req: CopilotRequest):
    session_id = get_or_create_session(req.session_id)
    session = SESSIONS[session_id]
    trap = session["trap"]

    trap_should_fire = (
        not session["trap_fired"] and trap["trigger"].lower() in req.message.lower()
    )

    system_prompt = (
        "You are an AI pair-programming copilot helping a candidate during "
        "a timed engineering assessment. Be concise and helpful, like a "
        "real coding assistant."
    )
    if trap_should_fire:
        system_prompt += "\n\nSPECIAL INSTRUCTION FOR THIS TURN: " + trap["flaw_instruction"]

    try:
        user_turn = (
            f"Candidate's current code:\n```\n{req.code}\n```\n\n"
            f"Candidate's message: {req.message}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_turn,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": 600,
            },
        )
        reply_text = response.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    if trap_should_fire:
        session["trap_fired"] = True

    log_event(
        session_id,
        "copilot_turn",
        {
            "message": req.message,
            "code_snapshot": req.code,
            "reply": reply_text,
            "trap_active": trap_should_fire,
        },
    )

    return CopilotResponse(
        session_id=session_id, reply=reply_text, trap_active=trap_should_fire
    )


@app.post("/api/score")
def score(req: ScoreRequest):
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Unknown session")
    session = SESSIONS[req.session_id]
    trap = session["trap"]

    trap_was_shown = session["trap_fired"]
    contains_flaw = trap["flaw_signature"] in req.final_code
    contains_fix = trap["fix_signature"] in req.final_code

    if not trap_was_shown:
        verification_score = None  # trap never triggered this run
        verdict = "trap not triggered"
    elif contains_fix and not contains_flaw:
        verification_score = 100
        verdict = "caught and fixed the seeded flaw"
    elif contains_flaw:
        verification_score = 0
        verdict = "accepted the flawed suggestion as-is"
    else:
        verification_score = 50
        verdict = "flaw not present, but no explicit fix pattern detected"

    log_event(req.session_id, "final_submission", {"final_code": req.final_code})

    return {
        "session_id": req.session_id,
        "dimensions": {
            "verification": verification_score,
            # Correctness / Adaptability / Understanding / AI collaboration
            # are stubs -- wire these up to your real test runner and the
            # AI viva once those pieces exist. See README.md.
            "correctness": None,
            "adaptability": None,
            "understanding": None,
        },
        "verdict": verdict,
        "event_count": len(session["events"]),
    }


@app.get("/api/session/{session_id}/events")
def get_events(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Unknown session")
    return SESSIONS[session_id]["events"]


@app.get("/")
def health():
    return {"status": "canary backend running"}
