
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import os
import requests


# ==========================================
# ENVIRONMENT VARIABLES
# ==========================================

MY_API_KEY = os.getenv("MY_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not MY_API_KEY:
    raise RuntimeError("MY_API_KEY is not configured.")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is not configured.")


# ==========================================
# CREATE FASTAPI APP
# ==========================================

app = FastAPI(
    title="Anurag AI API",
    description="Custom AI Chat API",
    version="3.0.0"
)


# ==========================================
# MEMORY
# ==========================================

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
# VERIFY API KEY
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
# HUGGING FACE AI
# ==========================================

def generate_response(prompt: str):

    model_name = "Qwen/Qwen2.5-0.5B-Instruct"

    url = (
        f"https://router.huggingface.co/hf-inference/"
        f"models/{model_name}"
    )

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9,
            "return_full_text": False
        }
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(
                f"Hugging Face API error: "
                f"{response.status_code} - {response.text}"
            )

        result = response.json()

        if isinstance(result, list) and len(result) > 0:

            return result[0].get(
                "generated_text",
                "I could not generate a response."
            ).strip()

        if isinstance(result, dict):

            if "error" in result:
                raise Exception(result["error"])

        return "I could not generate a response."

    except requests.exceptions.Timeout:

        raise Exception(
            "AI request timed out. Please try again."
        )


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Welcome to Anurag AI API",
        "status": "running",
        "version": "3.0.0"
    }


# ==========================================
# SIMPLE AI
# ==========================================

@app.post("/ai", response_model=AIResponse)
def ask_ai(
    request: AIRequest,
    x_api_key: str = Header(default=None)
):

    verify_api_key(x_api_key)

    prompt = request.prompt.strip()

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    try:

        result = generate_response(prompt)

        return {
            "response": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI error: {str(e)}"
        )


# ==========================================
# CHAT
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

    # Build conversation
    conversation_prompt = (
        "You are Anurag AI, a helpful and friendly AI assistant.\n\n"
    )

    for item in history:

        if item["role"] == "user":

            conversation_prompt += (
                f"User: {item['content']}\n"
            )

        elif item["role"] == "assistant":

            conversation_prompt += (
                f"Anurag AI: {item['content']}\n"
            )

    conversation_prompt += f"User: {message}\n"
    conversation_prompt += "Anurag AI:"

    try:

        response = generate_response(
            conversation_prompt
        )

        response = response.strip()

        # Save conversation
        history.append({
            "role": "user",
            "content": message
        })

        history.append({
            "role": "assistant",
            "content": response
        })

        return {
            "session_id": session_id,
            "response": response
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI error: {str(e)}"
        )


# ==========================================
# CLEAR MEMORY
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
        "message": "No conversation found",
        "session_id": session_id
    }


# ==========================================
# CHAT HISTORY
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


# ==========================================
# WEBSITE
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/website")
def website():

    return FileResponse(
        "static/index.html"
    )

