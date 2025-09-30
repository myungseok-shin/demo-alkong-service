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
            # "x-api-key": st.secrets["API_KEY"]
        }
        self.polling_interval = polling_interval

    def post_request_via_sse(self, input_data):
        target_url = f"{self.api_url}/{self.endpoint}/sse"

        # local_test 디렉토리가 없으면 생성
        os.makedirs('local_test', exist_ok=True)
        
        # 요청-응답 쌍을 저장할 데이터 구조
        chat_data = {
            'timestamp': datetime.now().isoformat(),
            'input': input_data,
            'output': None  # 응답이 오면 여기에 저장
        }
        
        # 기존 대화 내용 로드
        chat_log_file = 'local_test/chat_history.json'
        try:
            with open(chat_log_file, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            chat_history = []

        data = {
            "params_json": json.dumps(input_data, ensure_ascii=False),
            "callback_url": ""
        }

        try:
            # 먼저 히스토리에 입력 데이터 저장
            chat_history.append(chat_data)
            with open(chat_log_file, 'w', encoding='utf-8') as f:
                json.dump(chat_history, f, ensure_ascii=False, indent=2)

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
                    output_data['totalDuration'] = response_data.get('results', {}).get('totalDuration', 0)
                    
                    # sessionData 추출 및 업데이트
                    session_data = response_data.get('results', {}).get('sessionData', {})
                    if session_data:
                        # input_data에 sessionData 업데이트
                        if isinstance(input_data, dict) and 'inputData' in input_data:
                            input_data['inputData']['sessionData'] = session_data
                        else:
                            input_data['sessionData'] = session_data
                    
                    # 응답 데이터를 chat_data에 저장
                    chat_data['output'] = output_data
                    chat_data['session_data'] = session_data  # sessionData도 따로 저장
                    
                    # 히스토리의 마지막 항목(방금 저장한 입력)을 업데이트
                    chat_history[-1] = chat_data
                    
                    # 전체 히스토리를 파일로 저장
                    with open(chat_log_file, 'w', encoding='utf-8') as f:
                        json.dump(chat_history, f, ensure_ascii=False, indent=2)

                    return output_data
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 에러: {str(e)}")
                    print("원본 응답:")
                    print(response_text)
                    raise
        
            print("\n=== 예상치 못한 응답 형식 ===")
            print(response_text)
            print("=" * 50)
            raise Exception("응답이 'response:' 로 시작하지 않습니다.")
        except requests.RequestException as e:
            print(f"\n=== API 요청 실패 ===")
            print(f"에러: {str(e)}")
            print("=" * 50)
            raise

    async def post_request(self, input_data):
        target_url = f"{self.api_url}/{self.endpoint}"
        duration_test_url = f"{self.api_url}/alkong_duration_testtest"

        data = {
            "params_json": json.dumps(input_data, ensure_ascii=False),
            "callback_url": ""
        }

        print(f"\nPOST 요청 URL: {target_url}")
        print(f"POST 요청 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # SSL 검증 비활성화
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, headers=self.headers, data=data, ssl=ssl_context) as response: # 시간 테스트시 url 변경
                if response.status == 200:
                    response_data = await response.json()
                    print(f"POST 응답 데이터: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    return response_data
                else:
                    error_text = await response.text()
                    print(f"POST 에러 응답: {error_text}")
                    raise Exception(f"Failed to post api: Status {response.status}, Error: {error_text}")

    async def get_request(self, request_id):
        target_url = f"{self.api_url}/{self.endpoint}/{request_id}/status"
        duration_test_url = f"{self.api_url}/alkong_duration_testtest/{request_id}/status"
        start_time = datetime.now()
        poll_count = 0

        # SSL 검증 비활성화
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    poll_count += 1
                    async with session.get(target_url, headers=self.headers, ssl=ssl_context) as response:  # 시간 테스트시 url 변경
                        if response.status == 200:
                            result = await response.json()
                            if result['status'] == "COMPLETED":
                                end_time = datetime.now()
                                elapsed_time = (end_time - start_time).total_seconds()
                                result['results']['polling_info'] = {
                                    'elapsed_time': elapsed_time,
                                    'poll_count': poll_count
                                }
                                print(json.dumps(result, indent=4, ensure_ascii=False))
                                return result['results']
                            elif result['status'] == "FAILURE":
                                raise Exception(f"API 요청 실패: {result.get('failure_reason', 'Unknown error')}")
                            
                            await asyncio.sleep(self.polling_interval)
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to get api: Status {response.status}, Error: {error_text}")
                
                except aiohttp.ClientError as e:
                    raise Exception(f"API 요청 중 오류 발생: {str(e)}")
    
    async def _process_single_request(self, input_data):
        try:
            request_id = await self.post_request(input_data)
            print(f"\n요청 ID 수신: {request_id}")
            
            # POST 요청 후 최소 대기
            await asyncio.sleep(0.1)
            
            # 최대 5번 재시도, 지수 백오프 적용
            max_retries = 5
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    result = await self.get_request(request_id)
                    return result
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    if retry_count < max_retries:
                        # 지수 백오프: 0.1, 0.2, 0.4, 0.8, 1.6초
                        wait_time = 0.1 * (2 ** (retry_count - 1))
                        print(f"\n재시도 {retry_count}/{max_retries} - {str(e)} ({wait_time:.1f}초 대기)")
                        await asyncio.sleep(wait_time)
            
            raise Exception(f"최대 재시도 횟수 초과. 마지막 오류: {str(last_error)}")
        except Exception as e:
            raise Exception(f"API 요청 중 오류 발생: {str(e)}")

    def post_multiple_request(self, input_data: dict):
        """여러 데이터를 비동기로 평가 요청합니다."""
        try:
            print("\n=== 요청 처리 시작 ===")
            start_time = datetime.now()
            print(f"시작 시간: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
            
            # 비동기 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 단일 데이터를 리스트로 변환하여 처리
            items = [input_data]
            
            # 모든 요청을 비동기로 실행
            tasks = [self._process_single_request(item) for item in items]
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            
            # 결과 처리
            successful_results = []
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error processing item {idx}: {str(result)}")
                else:
                    successful_results.append(result)
            
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            print(f"종료 시간: {end_time.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"총 소요 시간: {elapsed_time:.3f}초")
            
            # 폴링 정보 출력
            for idx, result in enumerate(successful_results):
                if 'polling_info' in result:
                    print(f"요청 {idx+1} 폴링 횟수: {result['polling_info']['poll_count']}회")
            
            print("=== 요청 처리 완료 ===\n")
            
            return successful_results
            
        finally:
            loop.close()

################################


    # httpx를 사용하는 새로운 메서드들
    async def post_request_httpx(self, input_data):
        target_url = f"{self.api_url}/{self.endpoint}"
        duration_test_url = f"{self.api_url}/alkong_duration_testtest"

        data = {
            "params_json": json.dumps(input_data, ensure_ascii=False),
            "callback_url": ""
        }

        print(f"\n전송할 데이터 크기: {len(str(data))} bytes")
        print(f"요청 URL: {target_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # 요청 시작 직전 시간
                before_request = datetime.now()
                
                response = await client.post(target_url, headers=self.headers, data=data)
                response.raise_for_status()
                result = response.json()
                
                # 응답 받은 직후 시간
                after_request = datetime.now()
                network_time = (after_request - before_request).total_seconds()
                print(f"POST 요청 시간: {network_time:.3f}초")
                
                return result
            except httpx.HTTPStatusError as e:
                error_text = response.text
                raise Exception(f"Failed to post api: Status {response.status_code}, Error: {error_text}")
            except httpx.RequestError as e:
                raise Exception(f"Failed to post api: Network error: {str(e)}")

    async def get_request_httpx(self, request_id):
        target_url = f"{self.api_url}/{self.endpoint}/{request_id}/status"
        duration_test_url = f"{self.api_url}/alkong_duration_testtest/{request_id}/status"
        start_time = datetime.now()
        poll_count = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                try:
                    poll_count += 1
                    response = await client.get(target_url, headers=self.headers)
                    response.raise_for_status()
                    result = response.json()

                    if result['status'] == "COMPLETED":
                        end_time = datetime.now()
                        elapsed_time = (end_time - start_time).total_seconds()
                        print(json.dumps(result, indent=4, ensure_ascii=False))
                        return result['results']
                    elif result['status'] == "FAILURE":
                        raise Exception(f"API 요청 실패: {result.get('failure_reason', 'Unknown error')}")
                    
                    await asyncio.sleep(self.polling_interval)
                
                except httpx.HTTPStatusError as e:
                    error_text = response.text
                    raise Exception(f"Failed to get api: Status {response.status_code}, Error: {error_text}")
                except httpx.RequestError as e:
                    raise Exception(f"API 요청 중 오류 발생: Network error: {str(e)}")

    async def _process_single_request_httpx(self, input_data):
        try:
            # POST 요청 시작 시간
            post_start = datetime.now()
            request_id = await self.post_request_httpx(input_data)
            post_end = datetime.now()
            post_time = (post_end - post_start).total_seconds()
            print(f"\nPOST 요청 소요 시간: {post_time:.3f}초")
            
            # 대기 시작 시간
            wait_start = datetime.now()
            await asyncio.sleep(1)  # POST 요청 후 1초 대기
            wait_end = datetime.now()
            wait_time = (wait_end - wait_start).total_seconds()
            print(f"의도적 대기 시간: {wait_time:.3f}초")
            
            # GET 요청 시작
            get_start = datetime.now()
            result = await self.get_request_httpx(request_id)
            get_end = datetime.now()
            get_time = (get_end - get_start).total_seconds()
            print(f"GET 요청 소요 시간: {get_time:.3f}초")
            
            return result
        except Exception as e:
            raise Exception(f"API 요청 중 오류 발생: {str(e)}")

    def post_multiple_request_httpx(self, input_data: dict):
        """여러 데이터를 비동기로 평가 요청합니다. (httpx 사용)"""
        try:
            print("\n=== 요청 처리 시작 (httpx) ===")
            start_time = datetime.now()
            print(f"시작 시간: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            items = [input_data]
            tasks = [self._process_single_request_httpx(item) for item in items]
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            
            successful_results = []
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error processing item {idx}: {str(result)}")
                else:
                    successful_results.append(result)
            
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            print(f"종료 시간: {end_time.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"총 소요 시간: {elapsed_time:.3f}초")
            
            # 폴링 정보 출력
            for idx, result in enumerate(successful_results):
                if 'polling_info' in result:
                    print(f"요청 {idx+1} 폴링 횟수: {result['polling_info']['poll_count']}회")
            
            print("=== 요청 처리 완료 (httpx) ===\n")
            
            return successful_results
            
        finally:
            loop.close()


async def run_tests():
    chatbot_api = ChatbotAPI(polling_interval=0.3)
    # input_data = {
    #     "inputData": {
    #         "test": "test"
    #     }
    # }

    with open('chatbot_test_data/valid_test_data/첫인사생성.json', 'r') as f:
        input_data = json.load(f)
    input_data = {
        "inputData": input_data
    }
    
    # # # aiohttp 버전 테스트
    # print("\n=== aiohttp 버전 테스트 ===")
    # results = await chatbot_api._process_single_request(input_data)
    
    # httpx 버전 테스트
    print("\n=== httpx 버전 테스트 ===")
    results_httpx = await chatbot_api._process_single_request_httpx(input_data)

# if __name__ == "__main__":
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(run_tests())
#     finally:
#         loop.close()
