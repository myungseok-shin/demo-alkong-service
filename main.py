import streamlit as st
import json
from src.chatbot_api import ChatbotAPI
from datetime import datetime
import base64
from pathlib import Path
import asyncio
import time
import os

# 단계 매핑 딕셔너리
PHASE_MAPPING = {
    1: "인사",
    2: "종료",
    3: "일상대화",
    100: "탐색 (미사용)",
    200: "파악",
    300: "평가(자살/위험)",
    310: "학교폭력",
    320: "가정폭력",
    330: "정서",
    400: "긴급"
}

# 이미지 파일을 base64로 인코딩하는 함수
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded}"

# 아바타 이미지 로드 (절대 경로 사용)
current_dir = Path(__file__).parent
AI_AVATAR = get_image_base64(str(current_dir / "ryan.png"))
USER_AVATAR = get_image_base64(str(current_dir / "choonsik2.png"))

# 페이지 기본 설정
st.set_page_config(
    page_title="정서 상담 챗봇",
    page_icon="🤖",
    layout="wide"
)

# CSS 스타일 적용
st.markdown("""
<style>
    /* 전체 페이지 스타일링 */
    .main {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 0 20px !important;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        width: 300px !important;
    }
    
    /* 채팅 영역 스타일링 */
    .stChatMessageContainer {
        height: calc(85vh - 100px) !important;
        overflow-y: auto !important;
        padding: 2rem !important;
        background-color: #f8f9fa !important;
        border-radius: 10px !important;
        margin-bottom: 2rem !important;
    }
    
    /* 채팅 컨테이너 */
    .element-container {
        margin: 0.5rem 0 !important;
    }
    
    /* 채팅 컨테이너 스타일링 */
    .stChatFloatingInputContainer {
        padding-bottom: 60px !important;
    }
    
    /* 채팅 메시지 컨테이너 */
    .stChatMessageContainer {
        padding: 0 !important;
    }
    
    /* 메시지 공통 스타일 */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0 !important;
        margin: 15px 0 !important;
        gap: 8px !important;
    }
    
    /* 채팅 컨테이너 전체 스타일 */
    .stChatMessageContainer {
        padding: 1rem !important;
    }

    /* 메시지 컨테이너 공통 스타일 */
    [data-testid="stChatMessage"] {
        margin: 1rem 0 !important;
        position: relative !important;
        width: 100% !important;
    }

    /* 메시지 내용 공통 스타일 */
    [data-testid="stMarkdown"] {
        width: 100% !important;
    }

    [data-testid="stMarkdown"] > p {
        padding: 1rem 1.5rem !important;
        border-radius: 20px !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
        width: fit-content !important;
        max-width: 70% !important;
    }

    /* 사용자 메시지 스타일 */
    [data-testid="stChatMessage"].user {
        text-align: right !important;
    }

    [data-testid="stChatMessage"].user [data-testid="stMarkdown"] > p {
        margin-left: auto !important;
        background-color: #2979FF !important;
        color: white !important;
        border-bottom-right-radius: 5px !important;
    }

    [data-testid="stChatMessage"].user > div:first-child {
        position: absolute !important;
        right: 0 !important;
        margin-right: -50px !important;
    }

    /* AI 메시지 스타일 */
    [data-testid="stChatMessage"].assistant {
        text-align: left !important;
    }

    [data-testid="stChatMessage"].assistant [data-testid="stMarkdown"] > p {
        margin-right: auto !important;
        background-color: #F3F4F6 !important;
        color: #1F2937 !important;
        border-bottom-left-radius: 5px !important;
    }

    [data-testid="stChatMessage"].assistant > div:first-child {
        position: absolute !important;
        left: 0 !important;
        margin-left: -50px !important;
    }

    /* 아바타 스타일링 */
    [data-testid="stImage"] {
        width: 40px !important;
        height: 40px !important;
        border-radius: 50% !important;
    }
    
    /* AI 메시지 메타데이터 */
    .message-metadata {
        font-size: 12px !important;
        color: #374151 !important;
        margin-top: 4px !important;
        margin-left: 48px !important;
        font-weight: 500 !important;
    }
    
    /* 아바타 스타일링 */
    [data-testid="stImage"] {
        width: 40px !important;
        height: 40px !important;
        margin: 0 !important;
        border-radius: 50% !important;
        object-fit: cover !important;
    }
    
    /* 아바타 이미지 컨테이너 */
    [data-testid="stChatMessage"] > div:first-child {
        width: 40px !important;
        height: 40px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 입력창 스타일링 */
    .stChatInputContainer {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 20px !important;
        border-top: 1px solid #E5E7EB !important;
    }
    
    .stChatInputContainer textarea {
        border-radius: 25px !important;
        border: 1px solid #E5E7EB !important;
        padding: 12px 20px !important;
        font-size: 15px !important;
        box-shadow: none !important;
        resize: none !important;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #2979FF !important;
        box-shadow: 0 0 0 1px #2979FF !important;
    }
    
    /* 스크롤바 스타일링 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #D1D5DB;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9CA3AF;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chatbot_api' not in st.session_state:
    st.session_state.chatbot_api = ChatbotAPI(polling_interval=0.1)
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 1
if 'is_first_visit' not in st.session_state:
    st.session_state.is_first_visit = True
if 'current_history' not in st.session_state:
    st.session_state.current_history = []
if 'assessment_data' not in st.session_state:
    st.session_state.assessment_data = [
        {"assessmentId": i, "isAssessmentConfirmed": False, "isAssessmentCompleted": False} 
        for i in range(1, 6)
    ]
if 'issue_data' not in st.session_state:
    st.session_state.issue_data = []  # API 스펙에 맞춰 빈 배열로 초기화
if 'problem_data' not in st.session_state:
    st.session_state.problem_data = {
        "observationProblem": [],
        "confirmedProblem": []
    }  # API 스펙과 동일한 구조 유지
if 'last_displayed_message_index' not in st.session_state:
    st.session_state.last_displayed_message_index = 0
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# 사이드바 - 사용자 정보 입력
with st.sidebar:
    st.header("🧑‍💻 사용자 정보")
    user_name = st.text_input("이름", value="김춘식")
    user_age = st.number_input("나이", min_value=1, max_value=100, value=15)
    user_school = st.text_input("학교", value="제네시스랩 초등학교")
    user_grade = st.number_input("학년", min_value=1, max_value=6, value=3)
    user_class = st.number_input("반", min_value=1, max_value=20, value=4)

# 메타데이터 표시 함수
def display_metadata(metadata, is_polling=False):
    base_metadata = f"""
        빌더 응답 시간: {metadata.get('duration', '생성 중...')} | 
        총 소요 시간: {metadata.get('total_elapsed_time', '계산 중...')} | 
        현재 단계: {metadata.get('current_phase', '-')}({PHASE_MAPPING.get(metadata.get('current_phase', '-'), '알 수 없음')}) | 
        다음 단계: {metadata.get('next_phase', '생성 중...')}({PHASE_MAPPING.get(metadata.get('next_phase', '-'), '알 수 없음')}) | 
        심각도: {metadata.get('attention_level', '분석 중...')} | 
        대화 종료: {metadata.get('is_finished', '확인 중...')} | 
        자살 위험: {metadata.get('is_suicidal', '확인 중...')}
    """
    if is_polling and 'polling_info' in metadata:
        base_metadata = f"""
            {base_metadata.strip()} | 
            폴링 소요 시간: {metadata.get('polling_info', {}).get('elapsed_time', '계산 중...')}초 
            (총 {metadata.get('polling_info', {}).get('poll_count', '?')}회)
        """
    
    st.markdown(f"""<div class="message-metadata">{base_metadata}</div>""", unsafe_allow_html=True)

# 이전 메시지들만 표시하는 함수
def display_previous_messages(messages, chat_placeholder):
    for message in messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=AI_AVATAR):
                st.write(message["content"])
                if "metadata" in message:
                    display_metadata(message["metadata"], is_polling=False)
        else:
            with st.chat_message(message["role"], avatar=USER_AVATAR):
                st.write(message["content"])

# 전체 메시지 표시 함수
def display_messages(messages, chat_placeholder, is_polling=False):
    with chat_placeholder.container():
        for message in messages:
            if message["role"] == "assistant":
                with st.chat_message(message["role"], avatar=AI_AVATAR):
                    st.write(message["content"])
                    if "metadata" in message:
                        display_metadata(message["metadata"], is_polling)
            else:
                with st.chat_message(message["role"], avatar=USER_AVATAR):
                    st.write(message["content"])

# 메인 채팅 인터페이스
st.title("🤖 정서 상담 챗봇")

# 채팅 영역을 스크롤 가능한 컨테이너로 생성
chat_placeholder = st.empty()
display_messages(st.session_state.messages, chat_placeholder)

# API 요청 데이터 생성 함수
def create_input_data(user_name, user_age, user_school, user_grade, user_class, 
                     current_phase, current_history, is_first_visit, user_message=""):
    return {
        "inputData": {
            "chatRoomId": 123456778,
            "userId": 123456778,
            "userInfo": {
                "name": user_name,
                "age": user_age,
                "address": "서울시 중구 명동 제네시스랩",
                "phoneNumber": "010-1234-5678",
                "email": "ch.shin@genesislab.com",
                "schoolName": user_school,
                "grade": user_grade,
                "class": user_class,
                "homeroomTeacher": {
                    "name": "신명석",
                    "phoneNumber": "010-9876-5432",
                    "email": "ms.shin@genesislab.com"
                }
            },
            "conversationHistoryData": {
                "previousConversationData": [],
                "currentHistory": current_history
            },
            "userMessageData": {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": user_message
            },
            "sessionData": {
                "currentPhase": current_phase,
                "problemData": {
                    "observationProblem": [],
                    "confirmedProblem": []
                },  # API 스펙과 동일한 구조 유지
                "issueData": [],  # API 스펙에 맞춰 빈 배열로 초기화
                "assessmentData": [
                    {"assessmentId": i, "isAssessmentConfirmed": False, "isAssessmentCompleted": False} 
                    for i in range(1, 6)
                ],
                "attentionLevel": 1
            },
            "flagData": {
                "isFirstVisit": is_first_visit,
                "isConversationContinued": True,
                "isFinishedConversation": False,
                "isSuicideTendencyDetected": False
            },
            "additionalData": {
                "aiPersona": {
                    "id": 1,
                    "name": "김알콩",
                    "gender": "여성",
                    "personality": "대화 상대와 같은 또래이며 가상의 학교에 다니는 학생으로, 밝고 활발하며 공감 능력이 뛰어남. 때때로 본인의 현재 또는 과거 경험을 얘기하면서 친근한 말투로 대화를 이끌어 나감",
                    "formality": "반말"
                }
            }
        }
    }

# 첫 로드시 자동 메시지 생성
if not st.session_state.messages:
    
    # 요청 시작 시간 기록
    request_start_time = datetime.now()
    with st.chat_message("assistant", avatar=AI_AVATAR):
        with st.spinner("첫 인사 생성 중..."):
            # 첫 인사 요청 데이터 준비
            input_data = create_input_data(
                user_name=user_name,
                user_age=user_age,
                user_school=user_school,
                user_grade=user_grade,
                user_class=user_class,
                current_phase=st.session_state.current_phase,
                current_history=st.session_state.current_history,
                is_first_visit=st.session_state.is_first_visit
            )
            
            
            response = st.session_state.chatbot_api.post_request_via_sse(input_data)
            print("\n=== 응답 데이터 확인 ===")
            print(f"응답 타입: {type(response)}")
            print(f"응답 내용: {response}")
            
            
            # response: 형식의 문자열을 JSON으로 파싱
            if isinstance(response, str) and response.startswith("response:"):
                response = json.loads(response[len("response:"):].strip())
                print(f"파싱된 응답: {json.dumps(response, indent=2, ensure_ascii=False)}")
            if response and isinstance(response, dict):
                ai_message = response['aiMessageData']['message']
                total_duration = response['totalDuration']
                next_phase = response['sessionData']['nextPhase']
                attention_level = response['sessionData']['attentionLevel']

                # 전체 소요 시간 계산 (요청부터 응답 처리까지)
                response_time = datetime.now()
                total_elapsed_time = (response_time - request_start_time).total_seconds()
                
                # 챗봇 메시지와 메타데이터 저장
                new_message = {
                    "role": "assistant", 
                    "content": ai_message,
                    "metadata": {
                        "duration": total_duration,
                        "total_elapsed_time": total_elapsed_time,
                        "current_phase": st.session_state.current_phase,
                        "next_phase": next_phase,
                        "attention_level": attention_level,
                        "is_finished": response['flagData']['isFinishedConversation'],
                        "is_suicidal": response['flagData']['isSuicidalTendencyDetected']
                    }
                }
                st.session_state.messages.append(new_message)
                
                # AI 응답 스트리밍
                chat_placeholder.empty()
                with chat_placeholder.container():
                    # 이전 메시지들 표시 (마지막 메시지 제외)
                    display_previous_messages(st.session_state.messages[:-1], chat_placeholder)
                    # 새 메시지 스트리밍
                    with st.chat_message("assistant", avatar=AI_AVATAR):
                        message_placeholder = st.empty()
                        for j in range(len(ai_message) + 1):
                            message_placeholder.markdown(ai_message[:j] + "▌")
                            time.sleep(0.02)
                        message_placeholder.markdown(ai_message)
                        display_metadata(new_message["metadata"], is_polling=False)
                
                # 현재 대화 히스토리에 AI 응답 추가
                st.session_state.current_history.append({
                    "role": "ai",
                    "message": ai_message
                })
                
                # 세션 상태 업데이트
                st.session_state.current_phase = next_phase
                st.session_state.is_first_visit = False

# 사용자 입력 (처리 중일 때는 비활성화)
if prompt := st.chat_input("메시지를 입력하세요...", disabled=st.session_state.is_processing):
    # 요청 시작 시간 기록
    request_start_time = datetime.now()
    # 사용자 메시지 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자 입력 로깅

    
    # 사용자 메시지 즉시 표시
    chat_placeholder.empty()
    display_messages(st.session_state.messages, chat_placeholder, is_polling=True)

    # API 요청 데이터 준비
    input_data = create_input_data(
        user_name=user_name,
        user_age=user_age,
        user_school=user_school,
        user_grade=user_grade,
        user_class=user_class,
        current_phase=st.session_state.current_phase,
        current_history=st.session_state.current_history,
        is_first_visit=st.session_state.is_first_visit,
        user_message=prompt
    )

    # 처리 중 상태로 설정
    st.session_state.is_processing = True
    
    # 챗봇 응답 생성
    with st.spinner("생각 중..."):
            
            response = st.session_state.chatbot_api.post_request_via_sse(input_data)
            
            
            # response: 형식의 문자열을 파싱한 후에도 로깅
            if isinstance(response, str) and response.startswith("response:"):
                parsed_response = json.loads(response[len("response:"):].strip())

            # response: 형식의 문자열을 JSON으로 파싱
            if isinstance(response, str) and response.startswith("response:"):
                response = json.loads(response[len("response:"):].strip())
            # UI 표시 완료 시간 기록
            display_time = datetime.now()
            total_elapsed_time = (display_time - request_start_time).total_seconds()
            
            if response:
                ai_message = response['aiMessageData']['message']
                total_duration = response['totalDuration']
                next_phase = response['sessionData']['nextPhase']
                attention_level = response['sessionData']['attentionLevel']
                
                # 챗봇 메시지와 메타데이터 준비
                new_message = {
                    "role": "assistant", 
                    "content": ai_message,
                    "metadata": {
                        "duration": total_duration,
                        "total_elapsed_time": total_elapsed_time,
                        "current_phase": st.session_state.current_phase,
                        "next_phase": next_phase,
                        "attention_level": attention_level,
                        "is_finished": response['flagData']['isFinishedConversation'],
                        "is_suicidal": response['flagData']['isSuicidalTendencyDetected']
                    }
                }
                st.session_state.messages.append(new_message)
                
                # AI 응답 스트리밍
                chat_placeholder.empty()
                with chat_placeholder.container():
                    # 이전 메시지들 표시 (마지막 메시지 제외)
                    display_previous_messages(st.session_state.messages[:-1], chat_placeholder)
                    # 새 메시지 스트리밍
                    with st.chat_message("assistant", avatar=AI_AVATAR):
                        message_placeholder = st.empty()
                        for j in range(len(ai_message) + 1):
                            message_placeholder.markdown(ai_message[:j] + "▌")
                            time.sleep(0.02)
                        message_placeholder.markdown(ai_message)
                        display_metadata(new_message["metadata"], is_polling=False)
                
                # 대화 히스토리에 사용자 메시지와 AI 응답 추가
                st.session_state.current_history.append({
                    "role": "user",
                    "message": prompt
                })
                st.session_state.current_history.append({
                    "role": "ai",
                    "message": ai_message
                })
                
                # 세션 상태 업데이트
                st.session_state.current_phase = next_phase
                st.session_state.is_first_visit = False
                st.session_state.is_processing = False  # 처리 완료
                # 세션 데이터 업데이트
                print("\n=== 응답 데이터 확인 ===")
                print(f"응답의 assessmentData: {json.dumps(response['sessionData']['assessmentData'], indent=2, ensure_ascii=False)}")
                print(f"응답의 issueData: {json.dumps(response['sessionData']['issueData'], indent=2, ensure_ascii=False)}")
                print(f"응답의 problemData: {json.dumps(response['sessionData']['problemData'], indent=2, ensure_ascii=False)}")
                
                st.session_state.assessment_data = response['sessionData']['assessmentData']
                st.session_state.issue_data = response['sessionData']['issueData']
                st.session_state.problem_data = response['sessionData']['problemData']
                
                print("\n=== 업데이트 후 세션 상태 확인 ===")
                print(f"세션의 assessmentData: {json.dumps(st.session_state.assessment_data, indent=2, ensure_ascii=False)}")
                print(f"세션의 issueData: {json.dumps(st.session_state.issue_data, indent=2, ensure_ascii=False)}")
                print(f"세션의 problemData: {json.dumps(st.session_state.problem_data, indent=2, ensure_ascii=False)}")

# 채팅 영역 최종 업데이트 (스트리밍 없이)
chat_placeholder.empty()
display_messages(st.session_state.messages, chat_placeholder)