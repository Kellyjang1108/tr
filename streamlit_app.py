import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="학생 관리", page_icon="📚", layout="wide")

# 세션 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Google Sheets 연결
@st.cache_resource
def connect_sheets():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y/edit"
        return client.open_by_url(sheet_url)
    except:
        return None

# 데이터 읽기
def get_data(sheet_name):
    try:
        sheet = connect_sheets()
        if sheet:
            worksheet = sheet.worksheet(sheet_name)
            return pd.DataFrame(worksheet.get_all_records())
    except:
        pass
    return pd.DataFrame()

# 데이터 저장
def save_data(sheet_name, row_data):
    try:
        sheet = connect_sheets()
        if sheet:
            worksheet = sheet.worksheet(sheet_name)
            worksheet.append_row(row_data)
            return True
    except:
        pass
    return False

# 로그인 페이지
if not st.session_state.logged_in:
    st.title("📚 학생 관리 시스템")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login"):
            id = st.text_input("강사 ID")
            pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                df = get_data("강사_마스터")
                if not df.empty:
                    # 모든 값을 문자열로 변환
                    df['강사ID'] = df['강사ID'].astype(str)
                    df['비밀번호'] = df['비밀번호'].astype(str)
                    
                    valid = df[(df['teacher_id']==str(id)) & (df['password']==str(pw))]
                    if not valid.empty:
                        st.session_state.logged_in = True
                        st.session_state.teacher = valid.iloc[0]['name']
                        st.session_state.teacher_id = id
                        st.rerun()
                st.error("로그인 실패")

# 메인 앱
else:
    # 헤더
    col1, col2 = st.columns([3,1])
    with col1:
        st.title(f"👩‍🏫 {st.session_state.teacher} 선생님")
    with col2:
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["학생 목록", "출석 체크", "진도 입력"])
    
    # 학생 목록
    with tab1:
        st.subheader("📋 학생 목록")
        students = get_data("학생_마스터")
        if not students.empty:
            # 담당 학생만 표시
            if '담당강사ID' in students.columns:
                students = students[students['담당강사ID']==st.session_state.teacher_id]
            st.dataframe(students)
        else:
            st.info("학생 데이터가 없습니다")
    
    # 출석 체크
    with tab2:
        st.subheader("✅ 출석 체크")
        students = get_data("학생_마스터")
        
        if not students.empty:
            if '담당강사ID' in students.columns:
                students = students[students['담당강사ID']==st.session_state.teacher_id]
            
            for _, student in students.iterrows():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(student.get('이름', 'Unknown'))
                with col2:
                    if st.button("출석", key=f"p_{student.get('학생ID', _)}"):
                        save_data("출석_기록", [
                            datetime.now().strftime("%Y-%m-%d"),
                            student.get('학생ID', ''),
                            "출석",
                            datetime.now().strftime("%H:%M"),
                            "",
                            st.session_state.teacher_id,
                            ""
                        ])
                        st.success("✅")
                with col3:
                    if st.button("지각", key=f"l_{student.get('학생ID', _)}"):
                        save_data("출석_기록", [
                            datetime.now().strftime("%Y-%m-%d"),
                            student.get('학생ID', ''),
                            "지각",
                            datetime.now().strftime("%H:%M"),
                            "",
                            st.session_state.teacher_id,
                            ""
                        ])
                        st.warning("⏰")
                with col4:
                    if st.button("결석", key=f"a_{student.get('학생ID', _)}"):
                        save_data("출석_기록", [
                            datetime.now().strftime("%Y-%m-%d"),
                            student.get('학생ID', ''),
                            "결석",
                            "",
                            "",
                            st.session_state.teacher_id,
                            ""
                        ])
                        st.error("❌")
    
    # 진도 입력
    with tab3:
        st.subheader("📝 진도 입력")
        students = get_data("학생_마스터")
        
        if not students.empty:
            if '담당강사ID' in students.columns:
                students = students[students['담당강사ID']==st.session_state.teacher_id]
            
            names = students['이름'].tolist() if '이름' in students.columns else []
            if names:
                student_name = st.selectbox("학생 선택", names)
                
                col1, col2 = st.columns(2)
                with col1:
                    subject = st.selectbox("과목", ["단어", "문법", "독해"])
                    progress = st.text_input("진도", placeholder="예: 61-63일차")
                with col2:
                    rate = st.slider("완료율", 0, 100, 80)
                    memo = st.text_area("메모")
                
                if st.button("저장"):
                    student_id = students[students['이름']==student_name].iloc[0].get('학생ID', '')
                    save_data("일일_기록", [
                        f"R{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "",
                        student_id,
                        datetime.now().strftime("%Y-%m-%d"),
                        "출석",
                        progress,
                        f"{rate}%",
                        memo,
                        datetime.now().strftime("%H:%M")
                    ])
                    st.success("저장 완료!")
