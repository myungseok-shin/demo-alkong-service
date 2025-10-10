import streamlit as st
from datetime import datetime

def get_attention_level_info(phase, attention_level):
    """Phase와 attention level에 따른 색상과 라벨 반환"""
    if phase in [300, 400]:
        if attention_level == 100:
            return "#ffc107", "정서적 지지 필요"  # 노랑
        elif attention_level == 200:
            return "#fd7e14", "적극적 관심 필요"   # 주황
        elif attention_level == 300:
            return "#dc3545", "긴급 개입 필요"   # 빨강
    elif phase == 310:
        return "#dc3545", "학교폭력 피해 발견"
    elif phase == 320:
        return "#dc3545", "가정폭력 피해 발견"
    elif phase == 330:
        return "#fd7e14", "정서적 어려움"  # 초록
    else:
        return "#28a745", "양호"  # 초록

    # 기본값
    return "#6c757d", "확인 필요"

def display_student_basic_info(report_data):
    """학생 기본 정보 표시"""
    user_info = report_data['userInfo']
    created_at = report_data.get('createdAt', '')
    
    st.markdown("### 학생 정서 분석 리포트")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**{user_info['name']} ({user_info['schoolName']} {user_info['grade']}학년 {user_info['class']}반)**")
        if created_at:
            # ISO 형식 시간을 읽기 쉬운 형식으로 변환
            if 'T' in created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y년 %m월 %d일 %H시 %M분")
            else:
                formatted_time = created_at
            st.markdown(f"생성일시: {formatted_time}")
    
    with col2:
        st.markdown(f"**담임교사**: {user_info['homeroomTeacher']['name']}")
        st.markdown(f"연락처: {user_info['homeroomTeacher']['phoneNumber']}")

def display_final_assessment(final_assessment, phase):
    """최종 평가 및 권고 조치 표시"""
    
    st.markdown("### 최종 평가 및 권고 조치")

    color, label = get_attention_level_info(phase, final_assessment["attentionLevel"])
    combined_html = f"""
<div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
    <div style="width: 160px; height: 35px; background-color: {color}; 
                border-radius: 15px; display: flex; 
                align-items: center; justify-content: center;">
        <strong style="color: white; font-size: 14px;">{label}</strong>
    </div>
    <div style="height: 30px; display: flex; align-items: center;">
        <h5 style="margin: 0;">{final_assessment['finalAssessmentSummary']}</h5>
    </div>
</div>
"""
    st.markdown(combined_html, unsafe_allow_html=True)

    if phase in [1, 330]:
        # 핵심 상황 요약 (실제 데이터 사용)
        if phase in [300, 400]:
            summary_title = "주요 위험 정보 요약"
        elif phase in [310, 320]:
            summary_title = "폭력 피해 상황 요약"
        else:
            summary_title = "핵심 상황 요약"
        st.markdown(f"#### {summary_title}")
        
        col1, col2 = st.columns(2)
        
        # 좌측 컬럼과 우측 컬럼에 번갈아 배치
        for i, risk in enumerate(final_assessment['coreRiskSummary']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"**{risk['summaryName']}**")
                st.markdown(f"{risk['summaryResult']}")
                st.markdown("")
        
    
    elif phase in [300, 400]:
        # Phase 300/400: 자살 위험군      
        # 핵심 위험 요약 섹션
        summary_title = "핵심 위험 요약"
        st.markdown(f"#### {summary_title}")
        
        # 2컬럼 레이아웃으로 정렬
        col1, col2 = st.columns(2)
        
        # 좌측 컬럼과 우측 컬럼에 번갈아 배치
        for i, risk in enumerate(final_assessment['coreRiskSummary']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"**{risk['summaryName']}**")
                st.markdown(f"{risk['summaryResult']}")
                st.markdown("")  # 간격 추가
    
    elif phase in [310, 320]:
        # Phase 310: 학교 폭력, Phase 320: 가정 폭력
        # 핵심 문제 요약 섹션 (실제 데이터 사용)
        st.markdown("#### 핵심 문제 요약")
        
        col1, col2 = st.columns(2)
        
        # 좌측 컬럼과 우측 컬럼에 번갈아 배치
        for i, risk in enumerate(final_assessment['coreRiskSummary']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"**{risk['summaryName']}**")
                st.markdown(f"{risk['summaryResult']}")
                st.markdown("")
    
    else:
        # 기타 phase들에 대한 기본 처리
        # 핵심 상황 요약 섹션
        summary_title = "핵심 상황 요약"
        st.markdown(f"#### {summary_title}")
        
        col1, col2 = st.columns(2)
        
        for i, risk in enumerate(final_assessment['coreRiskSummary']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"**{risk['summaryName']}**")
                st.markdown(f"{risk['summaryResult']}")
                st.markdown("")
        
    # 지금 바로 행동해주세요 섹션
    if final_assessment.get('immediateActions'):
        st.markdown("#### 지금 바로 행동해 주세요.")
        actions_text = "\n".join([f"- {action}" for action in final_assessment['immediateActions']])
        st.markdown(actions_text)

def display_assessment_checklist(assessment_summary, phase):
    """핵심 요약 및 판단 근거 체크리스트 표시"""
    
    st.markdown("### 핵심 요약 및 판단 근거")
    
    if phase in [300, 400]:
        st.markdown("#### 자살 위기 체크리스트")
    elif phase in [310, 320]:
        st.markdown("#### 폭력 피해 상황")
    else:
        st.markdown("#### 항목별 분석 체크리스트")
    # 체크리스트를 container로 구분
    with st.container():
        # Phase 300/400인 경우만 O/X 표시 컬럼 추가
        if phase in [300, 400]:
            # 컬럼 헤더 표시 (Phase 300/400)
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.markdown("**평가 항목**")
            with col2:
                st.markdown("**판단**")
            with col3:
                st.markdown("**판단 근거**")
           
            # 체크리스트 형태로 표시
            for item in assessment_summary['checklist']:
                col1, col2, col3 = st.columns([2, 1, 3])
                
                with col1:
                    st.markdown(f"{item['assessmentName']}")
                
                with col2:
                    if item['assessmentResult'] == "True":
                        st.markdown("✅")
                    elif item['assessmentResult'] == "False":
                        st.markdown("❌")
                    else:
                        st.markdown("❓")
                
                with col3:
                    # Phase 300/400에서는 True/False 대신 의미있는 텍스트 표시
                    # 답변이 있는 경우 표시
                    if item.get('answers') and len(item['answers']) > 0 and item['answers'][0]:
                        if item['answers'][0] != "확인되지 않음":
                            for ans in item['answers']:
                                st.caption(f"- {ans}")
                    else:
                        st.caption(f"{item['answers'][0]}")
        else:
            # 다른 phase의 경우 O/X 표시 없음
            # 컬럼 헤더 표시 (다른 phase)
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.markdown("**확인 항목**")
            with col2:
                st.markdown("**분석 결과**")
            with col3:
                st.markdown("**주요 진술**")
            
            for item in assessment_summary['checklist']:
                col1, col2, col3 = st.columns([2, 1, 3])
                
                with col1:
                    st.markdown(item['assessmentName'])
                
                with col2:
                    # 간단한 결과 표시
                    st.markdown(item['assessmentResult'])
                
                with col3:
                    # 답변이 있는 경우 표시
                    if item.get('answers') and len(item['answers']) > 0 and item['answers'][0]:
                        if item['answers'][0] != "확인되지 않음":
                            for ans in item['answers']:
                                st.caption(f"- {ans}")
    
    st.markdown("---")
    
    # 위험 분석 (있는 경우)
    if assessment_summary.get('riskAnalysis'):
        st.markdown("#### 위험 분석")
        with st.container():
            for analysis in assessment_summary['riskAnalysis']:
                st.markdown(f"• {analysis}")
        st.markdown("---")

def display_situation_analysis(current_situation):
    """현재 상황 분석 표시"""
    
    st.markdown("### 현재 상황 분석")
    
    # 종합 분석 의견
    st.markdown("#### 종합 분석 의견")
    with st.container():
        st.markdown(current_situation['overallAnalysisOpinion'])
    
    
    # CSS로 info 박스 내부 텍스트 가운데 정렬
    st.markdown("""
    <style>
    .stAlert > div[data-baseweb="notification"] > div {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'emotionalKeywords' in current_situation:
        st.markdown("#### 감정 키워드 분석")
        with st.container():
            keywords = current_situation['emotionalKeywords']
            # 키워드 표시
            _, col0, _ = st.columns([1,3,1])
            with col0: 
                st.info(f"총 {keywords.get('studentMessageCount')}개의 문장에서 **부정 키워드 {keywords.get('negativeKeywordCount')}개**, **긍정 키워드 {keywords.get('positiveKeywordCount')}개**가 발견되었습니다.")
            negative_keywords = []
            negative_categories = []
            positive_categories = []
            positive_keywords = []

            for item in keywords['negativeKeywords']:
                if item["keywords"]:
                    negative_categories.append(item.get('category', ''))
                    negative_keywords.append(item.get('keywords', []))
            for item in keywords['positiveKeywords']:
                if item["keywords"]:
                    positive_categories.append(item.get('category', ''))
                    positive_keywords.append(item.get('keywords', []))

            col1, col2= st.columns(2)
            with col1:
                st.markdown("<div style='display: flex; justify-content: center;'><h5>&lt;부정 키워드&gt;</h5></div>", unsafe_allow_html=True)
                for cat, keywords in zip(negative_categories, negative_keywords):
                    st.metric(label=cat, value=', '.join(keywords))
            with col2:
                st.markdown("<div style='display: flex; justify-content: center;'><h5>&lt;긍정 키워드&gt;</h5></div>", unsafe_allow_html=True)
                for cat, keywords in zip(positive_categories, positive_keywords):
                    st.metric(label=cat, value=', '.join(keywords))

    
    # 환경 및 관계 분석
    if 'environmentAndRelationships' in current_situation:
        st.markdown("#### 환경 및 관계 분석")
        with st.container():
            env = current_situation['environmentAndRelationships']
            
            categories = [
                ("가족", env.get('family', '')),
                ("학교", env.get('school', '')), 
                ("친구", env.get('friends', '')),
                ("정서 및 생활 습관", env.get('emotionsAndLifestyle', '')),
                ("기타", env.get('others', ''))
            ]
            
            for category, content in categories:
                if content:
                    st.markdown(f"**{category}**: {content}")
        st.markdown("---")

def display_interests_and_approach(interests_data):
    """관심사 및 접근 방법 표시"""
    
    st.markdown("### 관심사 및 활용 방안")
    
    if interests_data.get('interests'):
        st.markdown("#### 관심사")
        with st.container():
            for interest in interests_data['interests']:
                st.markdown(f"• {interest}")
    
    if interests_data.get('approach'):
        st.markdown("#### 활용 방안")
        with st.container():
            for approach in interests_data['approach']:
                st.markdown(f"• {approach}")
        st.markdown("---")

def display_recommended_actions(actions_data):
    """권장 조치 및 다음 단계 표시"""
    
    st.markdown("### 권장 조치 및 다음 단계")
    
    # AI 권장사항
    if actions_data.get('aiSuggestions'):
        st.markdown("#### AI가 제안한 솔루션")
        with st.container():
            st.markdown(actions_data['aiSuggestions'])
    
    # 단기 조치
    if actions_data.get('shortTermActions'):
        st.markdown("#### 단기 조치")
        with st.container():
            for action in actions_data['shortTermActions']:
                st.markdown(f"• {action}")
    
    # 장기 조치  
    if actions_data.get('longTermActions'):
        st.markdown("#### 장기 조치")
        with st.container():
            for action in actions_data['longTermActions']:
                st.markdown(f"• {action}")
        st.markdown("---")

def display_report_page(report_data):
    """리포트 페이지 메인 함수"""
    
    if not report_data:
        st.warning("리포트 데이터가 없습니다. 먼저 리포트를 생성해주세요.")
        return
    
    st.markdown("""
<style>
    /* 마지막 컬럼 제외하고 오른쪽에 선 추가 */
    [data-testid="column"]:not(:last-child) {
        border-right: 2px solid #e0e0e0;
        padding-right: 20px;
        margin-right: 20px;
    }
</style>
""", unsafe_allow_html=True)
    
    phase = report_data.get('phase', 1)
    
    # 페이지 레이아웃
    st.markdown("---")
    
    # 기본 정보
    display_student_basic_info(report_data)
    
    st.markdown("---")
    
    # 최종 평가
    if 'finalAssessment' in report_data:
        display_final_assessment(report_data['finalAssessment'], phase)
        st.markdown("---")
    
    # 평가 체크리스트
    if 'assessmentSummary' in report_data:
        display_assessment_checklist(report_data['assessmentSummary'], phase)
    
    # 현재 상황 분석
    if 'currentSituationAnalysis' in report_data:
        display_situation_analysis(report_data['currentSituationAnalysis'])
    
    # 관심사 및 접근 방법
    if 'interestsAndApproach' in report_data:
        display_interests_and_approach(report_data['interestsAndApproach'])
    
    # 권장 조치
    if 'recommendedActions' in report_data:
        display_recommended_actions(report_data['recommendedActions'])