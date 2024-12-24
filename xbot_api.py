# -*- coding:utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from io import BytesIO
import requests
from libExcel import read_excel

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


class OpenRouterRequest(BaseModel):
    system_prompt: str
    user_prompt: str



@app.post("/openrouter")
async def openrouter_query(request: OpenRouterRequest):
    payload = {
        "model": "gpt-4o-mini",
        "prompt": [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt}
        ],
        "max_tokens": 1024
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
        # openrouter_response = await openrouter_query(
        #     OpenRouterRequest(system_prompt=system_prompt, user_prompt=user_prompt))
        # reply += f"Bot: {openrouter_response['reply']}"
        reply += f"Bot: {message}"
    if file:
        file_extension = file.filename.split('.')[-1]
        if file_extension in ['xlsx', 'xls']:
            file_bytes = await file.read()
            data = read_excel(BytesIO(file_bytes))
            system_prompt = "You are a helpful assistant."
            user_prompt = message
            reply += f" and uploaded {file_extension} file '{file.filename}' with content: {data}"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx and .xls files are allowed.")
    return {"reply": reply}