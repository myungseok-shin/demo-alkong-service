import streamlit as st
import json
import time
from datetime import datetime
from src.report_api import ReportAPI
from src.summary_api import ChatSummaryAPI
from src.report_display import display_report_page


st.set_page_config(
    page_title="세션 결과 요약 및 리포트 생성",
    layout="wide"
)

if 'session_data' not in st.session_state:
    st.warning("세션 데이터가 없습니다. 먼저 대화를 시작하세요.")
    st.stop()

st.title("세션 결과 요약 및 리포트 생성")

if 'summary_results' not in st.session_state:
    st.session_state['summary_results'] = None
if 'report_results' not in st.session_state:
    st.session_state['report_results'] = None

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

def create_report_input_data():
    # 마지막 AI 메시지의 metadata를 찾음
    last_ai_message = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and "metadata" in msg:
            last_ai_message = msg
            break
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
            "phase": last_ai_message["metadata"]["next_phase"] if last_ai_message else st.session_state.current_phase,
            "conversationHistory": st.session_state.current_history,
            "isEmergency": False,
            "aiSuggestions": st.session_state.summary_results["aiSuggestions"],
            "assessmentData": st.session_state.summary_results["assessmentData"],
            "attentionLevel": last_ai_message["metadata"]["attention_level"] if last_ai_message else 1,
        }
    }


col1, col2 = st.columns(2)

with col1:
    if st.button("요약 생성"):
        chat_summary_api = ChatSummaryAPI()
        input_data = create_summary_input_data()
        st.session_state['summary_results'] = chat_summary_api.post_request_via_sse(input_data)
        if st.session_state['summary_results']:
            st.success("요약 생성 완료!")
        else:
            st.error("요약 생성 실패!")
    
    # 요약 결과가 있으면 표시
    if st.session_state.get('summary_results'):
        st.success("요약 생성 완료!")
        st.json(st.session_state['summary_results'], expanded=True)

with col2:
    if st.session_state.get('summary_results'):
        if st.button("리포트 생성"):
            report_api = ReportAPI()
            input_data = create_report_input_data()
            st.session_state["report_results"] = report_api.post_request_via_sse(input_data)
            if not st.session_state['report_results']:
                st.error("리포트 생성 실패!")
        
        # 리포트 결과가 있으면 표시
        if st.session_state.get('report_results'):
            st.success("리포트 생성 완료!")
            st.json(st.session_state['report_results'], expanded=True)

# 리포트 보기 버튼은 별도로 배치
if st.session_state.get('report_results'):
    st.markdown("---")
    if st.button("📄 상세 리포트 보기"):
        display_report_page(st.session_state['report_results'])

if not st.session_state.get('summary_results'):
    st.info("대화 진행 후 요약을 생성하면 리포트를 생성할 수 있습니다.")