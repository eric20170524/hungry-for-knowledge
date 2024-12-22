from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from io import BytesIO
import requests

app = FastAPI()

# 允许 CORS 请求
origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter API Key
OPENROUTE_API_KEY = 'your_openroute_api_key'


class OpenRouterRequest(BaseModel):
    system_prompt: str
    user_prompt: str


def read_excel(file_bytes, file_type):
    df = pd.read_excel(BytesIO(file_bytes), engine='openpyxl' if file_type == 'xlsx' else 'xlrd')
    return df.to_dict()


@app.post("/openrouter")
async def openrouter_endpoint(request: OpenRouterRequest):
    payload = {
        "prompt": [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt}
        ],
        "max_tokens": 50
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        'https://api.openrouter.ai/v1/chat/completions',
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        response_data = response.json()
        return {"reply": response_data['choices'][0]['text']}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to get response from OpenRouter")


@app.post("/chat")
async def chat_endpoint(message: str = Form(None), file: UploadFile = File(None)):
    reply = ""
    if message:
        system_prompt = "You are a helpful assistant."
        user_prompt = message
        # openrouter_response = await openrouter_endpoint(
        #     OpenRouterRequest(system_prompt=system_prompt, user_prompt=user_prompt))
        # reply += f"Bot: {openrouter_response['reply']}"
        reply += f"Bot: {message}"
    if file:
        file_extension = file.filename.split('.')[-1]
        if file_extension in ['xlsx', 'xls']:
            file_bytes = await file.read()
            data = read_excel(file_bytes, file_extension)
            reply += f" and uploaded {file_extension} file '{file.filename}' with content: {data}"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx and .xls files are allowed.")
    return {"reply": reply}