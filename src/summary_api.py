import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import streamlit as st
load_dotenv()

class ChatSummaryAPI:
    def __init__(self, polling_interval=0.2):  # polling 간격 최적화
        # self.api_key = os.getenv("API_KEY")
        # self.endpoint = os.getenv("SUMMARY_ENDPOINT")
        # self.api_url = os.getenv("API_URL")
        self.api_key = st.secrets["API_KEY"]
        self.endpoint = st.secrets["SUMMARY_ENDPOINT"]
        self.api_url = st.secrets["API_URL"]
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        self.polling_interval = polling_interval

    def post_request_via_sse(self, input_data):
        target_url = f"{self.api_url}/{self.endpoint}/sse"

        # local_test 디렉토리가 없으면 생성
        os.makedirs('local_test', exist_ok=True)
        
        # 요청-응답 쌍을 저장할 데이터 구조
        summary_data = {
            'timestamp': datetime.now().isoformat(),
            'input': input_data,
            'output': None  # 응답이 오면 여기에 저장
        }
        
        data = {
            "params_json": json.dumps(input_data, ensure_ascii=False),
            "callback_url": ""
        }

        try:
            response = requests.post(target_url, headers=self.headers, data=data)
            response.raise_for_status()  # HTTP 에러 체크
            response_text = response.text
            
            print("\n=== 원본 응답 ===")
            print(response_text)
            print("=" * 50)
            
            # response: 부분을 제거하고 JSON 파싱
            if response_text.startswith("response:"):
                json_str = response_text[len("response:"):].strip()
                try:
                    response_data = json.loads(json_str)
                    print("\nPOST 응답 데이터 (parsed):")
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
                    print("-" * 50)
                    # results.outputData와 totalDuration을 합쳐서 반환
                    output_data = response_data.get('results', {}).get('outputData', {})
                    # 응답 데이터를 summary_data에 저장
                    summary_data['output'] = output_data
                    print("\n=== 파싱 결과 ===")
                    print(json.dumps(output_data, indent=2, ensure_ascii=False))
                    return output_data
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 에러: {str(e)}")
                    print("원본 응답:")
                    print(response_text)
                    raise ValueError("응답 JSON 파싱 실패")
        
            print("\n=== 예상치 못한 응답 형식 ===")
            print(response_text)
            print("=" * 50)
            raise Exception("응답이 'response:' 로 시작하지 않습니다.")
        except requests.RequestException as e:
            print(f"\n=== API 요청 실패 ===\n 에러: {str(e)}")
            print("=" * 50)
            raise

if __name__ == "__main__":
    chat_summary_api = ChatSummaryAPI()
    with open('summary_test_data/요약생성.json', 'r') as f:
        input_data = json.load(f)
    input_data = {
        "inputData": input_data
    }
    print(f"Input Data: {input_data}")
    results = chat_summary_api.post_request_via_sse(input_data)
    print(results)