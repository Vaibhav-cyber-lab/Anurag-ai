#python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from model import generate_response


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")


# Check API key configuration
if not MY_API_KEY:
    raise RuntimeError(
        "MY_API_KEY not found. Please create a .env file."
    )


# ==========================================
# CREATE FASTAPI APP
# ==========================================

app = FastAPI(
    title="Anurag AI API",
    description="Custom AI Chat API with API key authentication",
    version="2.0.0"
)


# ==========================================
# MEMORY
# ==========================================

# Stores conversation history for each session
conversation_memory = {}


# ==========================================
# REQUEST MODELS
# ==========================================

class AIRequest(BaseModel):
    prompt: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class AIResponse(BaseModel):
    response: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Welcome to Anurag AI API",
        "status": "running",
        "version": "2.0.0"
    }


# ==========================================
# API KEY VERIFICATION
# ==========================================

def verify_api_key(x_api_key: str):

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required"
        )

    if x_api_key != MY_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


# ==========================================
# SIMPLE AI ENDPOINT
# ==========================================

@app.post("/ai", response_model=AIResponse)
def ask_ai(
    request: AIRequest,
    x_api_key: str = Header(default=None)
):

    verify_api_key(x_api_key)

    try:
        result = generate_response(request.prompt)

        return {
            "response": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI model error: {str(e)}"
        )


# ==========================================
# CHAT ENDPOINT
# ==========================================
@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    x_api_key: str = Header(default=None)
):

    verify_api_key(x_api_key)

    session_id = request.session_id
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    # Create session
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []

    history = conversation_memory[session_id]

    # Save user message
    history.append({
        "role": "user",
        "content": message
    })

    # Build conversation
    conversation_prompt = ""

    for item in history:

        if item["role"] == "user":

            conversation_prompt += (
                f"User: {item['content']}\n"
            )

        elif item["role"] == "assistant":

            conversation_prompt += (
                f"Anurag AI: {item['content']}\n"
            )

    try:

        response = generate_response(
            conversation_prompt
        )

        response = response.strip()

        # Save AI response
        history.append({
            "role": "assistant",
            "content": response
        })

        return {
            "session_id": session_id,
            "response": response
        }

    except Exception as e:

        # Remove failed user message
        if history and history[-1]["role"] == "user":
            history.pop()

        raise HTTPException(
            status_code=500,
            detail=f"AI model error: {str(e)}"
        )

    # Create a new conversation if session doesn't exist
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []

    # Get previous conversation
    history = conversation_memory[session_id]

    # Add current user message
    history.append({
        "role": "user",
        "content": message
    })

    # Create conversation prompt
    conversation_prompt = ""

    for item in history:
        if item["role"] == "user":
            conversation_prompt += f"User: {item['content']}\n"

        elif item["role"] == "assistant":
            conversation_prompt += f"Anurag AI: {item['content']}\n"

    conversation_prompt += "Anurag AI:"

    try:

        # Generate AI response
        response = generate_response(conversation_prompt)

        response = response.strip()

        # Save AI response in memory
        history.append({
            "role": "assistant",
            "content": response
        })

        return {
            "session_id": session_id,
            "response": response
        }

    except Exception as e:

        # Remove user message if model fails
        if history and history[-1]["role"] == "user":
            history.pop()

        raise HTTPException(
            status_code=500,
            detail=f"AI model error: {str(e)}"
        )


# ==========================================
# CLEAR CHAT MEMORY
# ==========================================

@app.delete("/clear-memory/{session_id}")
def clear_memory(
    session_id: str,
    x_api_key: str = Header(default=None)
):

    verify_api_key(x_api_key)

    if session_id in conversation_memory:
        del conversation_memory[session_id]

        return {
            "message": "Conversation memory cleared",
            "session_id": session_id
        }

    return {
        "message": "No conversation found for this session",
        "session_id": session_id
    }


# ==========================================
# VIEW CHAT HISTORY
# ==========================================

@app.get("/history/{session_id}")
def get_history(
    session_id: str,
    x_api_key: str = Header(default=None)
):

    verify_api_key(x_api_key)

    return {
        "session_id": session_id,
        "history": conversation_memory.get(
            session_id,
            []
        )
    }
# Serve website files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/website")
def website():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/website")
def website():
    return FileResponse("static/index.html")
