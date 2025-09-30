import requests
import os
import ssl
from dotenv import load_dotenv
import asyncio
import aiohttp
import json
from datetime import datetime
import httpx  # httpx 추가
import streamlit as st
load_dotenv()

class ChatbotAPI:
    def __init__(self, polling_interval=0.2):  # polling 간격 최적화
        # self.api_key = os.getenv("API_KEY")
        # self.endpoint = os.getenv("ENDPOINT")
        # self.api_url = os.getenv("API_URL")
        self.api_key = st.secrets["API_KEY"]
        self.endpoint = st.secrets["ENDPOINT"]
        self.api_url = st.secrets["API_URL"]
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        self.polling_interval = polling_interval

    async def post_via_sse(self, input_data):
        target_url = f"{self.api_url}/{self.endpoint}/sse"

        data = {
            "params_json": json.dumps(input_data, ensure_ascii=False),
            "callback_url": ""
        }

        response = requests.post(target_url, headers=self.headers, data=data)
        response_text = response.text
        
        # response: 부분을 제거하고 JSON 파싱
        if response_text.startswith("response:"):
            json_str = response_text[len("response:"):].strip()
            try:
                response_data = json.loads(json_str)
                print("\nPOST 응답 데이터 (parsed):")
                # print(json.dumps(response_data, indent=2, ensure_ascii=False))
                print(response_data['results']['outputData'])
                print("-" * 50)
                return response_data['results']['outputData']
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 에러: {str(e)}")
                print("원본 응답:")
                print(response_text)
                raise
        
        return response_text


if __name__ == "__main__":
    chatbot_api = ChatbotAPI()
    with open('chatbot_test_data/valid_test_data/첫인사생성.json', 'r') as f:
        input_data = json.load(f)
    input_data = {
        "inputData": input_data
    }
    results = asyncio.run(chatbot_api.post_via_sse(input_data))
    print(results)