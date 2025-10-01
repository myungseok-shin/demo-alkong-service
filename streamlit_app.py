import streamlit as st
import json
from src.chatbot_api import ChatbotAPI
from src.summary_api import ChatSummaryAPI
from datetime import datetime
import base64
from pathlib import Path
import asyncio
import time
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="정서 상담 챗봇",
    page_icon="🤖",
    layout="wide"
)

# Load whitelist from Streamlit secrets
try:
    white_list = st.secrets["whitelist"]["allowed_users"]
except KeyError:
    # 개발 환경을 위한 기본값 설정
    if st.secrets.get("dev_mode", False):
        st.warning("⚠️ 개발 모드: 기본 화이트리스트를 사용합니다")
        white_list = [{"name": "테스트사용자"}, {"name": "admin"}]
    else:
        st.error("화이트리스트 설정이 필요합니다. Streamlit secrets에 whitelist 설정을 추가해주세요.")
        st.stop()

# 화이트리스트 검증 (개발 모드가 아닐 때만)
if not st.secrets.get("dev_mode", False):
    user_name = st.text_input("이름 입력")
    if not user_name:
        st.warning("이름을 입력해주세요.")
        st.stop()
    elif not any(u["name"] == user_name for u in white_list):
        st.error("허용되지 않은 사용자입니다.")
        st.stop()
    else:
        st.success(f"{user_name} 접근 허용")

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
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 800px !important;
        background: white !important;
        padding: 20px !important;
        border-top: 1px solid #E5E7EB !important;
        box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    div[data-testid="stChatInput"] > div {
        width: 100% !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        border-radius: 25px !important;
        border: 1px solid #E5E7EB !important;
        padding: 12px 20px !important;
        font-size: 15px !important;
        box-shadow: none !important;
        resize: none !important;
        width: 100% !important;
        background: #f8f9fa !important;
    }
    
    /* 채팅 영역 하단 여백 */
    .stChatMessageContainer {
        margin-bottom: 80px !important;
    }
    
    /* 메인 컨텐츠 영역 패딩 추가 */
    .main .block-container {
        padding-bottom: 100px !important;
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

    /* 응답 데이터 드롭다운 스타일 */
    .response-data-container {
        margin-top: 10px;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 10px;
        background-color: #F9FAFB;
    }
    
    .response-data-header {
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    }
    
    .response-data-content {
        font-family: monospace;
        font-size: 14px;
        white-space: pre-wrap;
        color: #1F2937;
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
        {"assessmentId": 10, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 20, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 30, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 31, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 32, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 33, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 40, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 41, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
        {"assessmentId": 50, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False}
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
if 'session_data' not in st.session_state:
    st.session_state.session_data = {}
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 1
if 'next_phase' not in st.session_state:
    st.session_state.next_phase = 1
if 'summary_results' not in st.session_state:
    st.session_state['summary_results'] = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = int(time.time() * 1000000)

def create_summary_input_data():
# 마지막 AI 메시지의 metadata를 찾음
    last_ai_message = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and "metadata" in msg:
            last_ai_message = msg
            break
    session_data = {
        "currentPhase": last_ai_message["metadata"]["next_phase"] if last_ai_message else st.session_state.current_phase,
        "problemData": st.session_state.problem_data,
        "issueData": st.session_state.issue_data,
        "assessmentData": st.session_state.assessment_data,
        "attentionLevel": last_ai_message["metadata"]["attention_level"] if last_ai_message else 1
    }
    return {
        "inputData": {
            "chatRoomId": st.session_state.session_id,
            "userId": 123456778,
            "userInfo": {
                "name": st.session_state.user_name,
                "age": st.session_state.user_age,
                "address": "서울시 중구 명동 제네시스랩",
                "phoneNumber": "010-1234-5678",
                "email": "ch.shin@genesislab.com",
                "schoolName": st.session_state.user_school,
                "grade": st.session_state.user_grade,
                "class": st.session_state.user_class,
                "homeroomTeacher": {
                    "name": "신명석",
                    "phoneNumber": "010-9876-5432",
                    "email": "ms.shin@genesislab.com"
                }
            },
            "conversationHistory": st.session_state.current_history,
            "sessionData": session_data | {"nextPhase" : last_ai_message["metadata"]["next_phase"]},
            "personaId": 1
        }
    }


# 사이드바 - 사용자 정보 입력
with st.sidebar:
    st.header("🧑‍💻 사용자 정보")
    user_name = st.text_input("이름", value="김춘식")
    user_age = st.number_input("나이", min_value=1, max_value=100, value=10)
    user_school = st.text_input("학교", value="제네시스랩 초등학교")
    user_grade = st.number_input("학년", min_value=1, max_value=6, value=3)
    user_class = st.number_input("반", min_value=1, max_value=20, value=4)
    
    st.header("🤖 AI 페르소나 설정")
    ai_personality = st.text_area(
        "AI 성격",
        value="대화 상대와 같은 또래이며 가상의 학교에 다니는 학생으로, 밝고 활발하며 공감 능력이 뛰어남. 때때로 본인의 현재 또는 과거 경험을 얘기하면서 친근한 말투로 대화를 이끌어 나감",
        height=150
    )
    ai_formality = st.text_input(
        "말투",
        value="반말",
        help="예: 반말, 존댓말, 친근한 말투 등"
    )
    
    st.session_state['user_name'] = user_name
    st.session_state['user_age'] = user_age
    st.session_state['user_school'] = user_school
    st.session_state['user_grade'] = user_grade
    st.session_state['user_class'] = user_class
    st.session_state['ai_personality'] = ai_personality
    st.session_state['ai_formality'] = ai_formality
    

    if st.button("요약 생성"):
        if len(st.session_state.messages) > 2:
            chat_summary_api = ChatSummaryAPI()
            input_data = create_summary_input_data()
            st.session_state['summary_results'] = chat_summary_api.post_request_via_sse(input_data)
            if st.session_state['summary_results']:
                st.success("요약 생성 완료!")
                st.markdown("summary and report 페이지에서 요약을 확인하세요.")
                # st.json(st.session_state['summary_results'], expanded=True)
            else:
                st.error("요약 생성 실패!")
        else:
            st.warning("먼저 대화를 진행해주세요.")

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
                if "response_data" in message:
                    with st.expander("🔍 응답 데이터 보기", expanded=False):
                        st.json(message["response_data"]["sessionData"])
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
                    if "response_data" in message:
                        with st.expander("🔍 응답 데이터 보기", expanded=False):
                            st.json(message["response_data"]["sessionData"])
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
    # 첫 인사일 때는 초기 sessionData 사용
    if is_first_visit:
        session_data = {
            "currentPhase": current_phase,
            "problemData": {
                "observationProblem": [],
                "confirmedProblem": []
            },
            "issueData": [],
                "assessmentData": [
                    {"assessmentId": 10, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 20, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 30, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 31, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 32, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 33, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 40, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 41, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False},
                    {"assessmentId": 50, "isAssessmentConfirmed": False, "isAssessmentCompleted": False, "isValidAnswered": False}
                ],
            "attentionLevel": 1
        }
    else:
        # 이전 응답의 sessionData 사용
        # 마지막 AI 메시지의 metadata를 찾음
        last_ai_message = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant" and "metadata" in msg:
                last_ai_message = msg
                break
        
        session_data = {
            "currentPhase": last_ai_message["metadata"]["next_phase"] if last_ai_message else current_phase,
            "problemData": st.session_state.problem_data,
            "issueData": st.session_state.issue_data,
            "assessmentData": st.session_state.assessment_data,
            "attentionLevel": last_ai_message["metadata"]["attention_level"] if last_ai_message else 1
        }

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
            "sessionData": session_data,
            "flagData": {
                "isFirstVisit": is_first_visit,
                "isConversationContinued": is_first_visit,  # 첫 턴에만 True, 이후에는 False
                "isFinishedConversation": False,
                "isSuicideTendencyDetected": False
            },
            "additionalData": {
                "aiPersona": {
                    "id": 1,
                    "name": "김알콩",
                    "gender": "여성",
                    "personality": st.session_state.get('ai_personality', "대화 상대와 같은 또래이며 가상의 학교에 다니는 학생으로, 밝고 활발하며 공감 능력이 뛰어남. 때때로 본인의 현재 또는 과거 경험을 얘기하면서 친근한 말투로 대화를 이끌어 나감"),
                    "formality": st.session_state.get('ai_formality', "반말")
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
                    },
                    "response_data": response
                }
                st.session_state.messages.append(new_message)
                
                # AI 응답 스트리밍
                chat_placeholder.empty()
                with chat_placeholder.container():
                    # 이전 메시지들 표시 (마지막 메시지 제외)
                    display_previous_messages(st.session_state.messages[:-1], chat_placeholder)
                    # 새 메시지 스트리밍
                    with st.chat_message("assistant", avatar=AI_AVATAR):
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            message_placeholder = st.empty()
                            for j in range(len(ai_message) + 1):
                                message_placeholder.markdown(ai_message[:j] + "▌")
                                time.sleep(0.02)
                            message_placeholder.markdown(ai_message)
                            display_metadata(new_message["metadata"], is_polling=False)
                        
                        with col2:
                            with st.expander("🔍", expanded=False):
                                st.markdown("### 응답 데이터")
                                st.json(response)
                
                # 현재 대화 히스토리에 AI 응답 추가
                st.session_state.current_history.append({
                    "role": "ai",
                    "message": ai_message,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # 세션 상태 업데이트
                st.session_state.current_phase = next_phase
                st.session_state.session_data = response['sessionData']
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
                    },
                    "response_data": response
                }
                st.session_state.messages.append(new_message)
                
                # AI 응답 스트리밍
                chat_placeholder.empty()
                with chat_placeholder.container():
                    # 이전 메시지들 표시 (마지막 메시지 제외)
                    display_previous_messages(st.session_state.messages[:-1], chat_placeholder)
                    # 새 메시지 스트리밍
                    with st.chat_message("assistant", avatar=AI_AVATAR):
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            message_placeholder = st.empty()
                            for j in range(len(ai_message) + 1):
                                message_placeholder.markdown(ai_message[:j] + "▌")
                                time.sleep(0.02)
                            message_placeholder.markdown(ai_message)
                            display_metadata(new_message["metadata"], is_polling=False)
                        
                        with col2:
                            with st.expander("🔍", expanded=False):
                                st.markdown("### 응답 데이터")
                                st.json(response)
                
                # 대화 히스토리에 사용자 메시지와 AI 응답 추가
                st.session_state.current_history.append({
                    "role": "user",
                    "message": prompt,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.current_history.append({
                    "role": "ai",
                    "message": ai_message,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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