import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="학생관리", page_icon="📚")

# 초기화
if 'login' not in st.session_state:
    st.session_state.login = False

# 구글시트 연결 (테스트에서 작동한 코드)
@st.cache_resource
def connect():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_key("1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y")

# 데이터 읽기
def read(sheet_name):
    try:
        sheet = connect()
        data = sheet.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# 데이터 쓰기
def write(sheet_name, row):
    try:
        sheet = connect()
        sheet.worksheet(sheet_name).append_row(row)
        return True
    except:
        return False

# 로그인
if not st.session_state.login:
    st.title("📚 학생관리 시스템")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("로그인")
        id = st.text_input("ID")
        pw = st.text_input("비밀번호", type="password")
        
        if st.button("로그인", use_container_width=True):
            df = read("강사_마스터")
            
            if not df.empty:
                # 컬럼명 무시하고 위치로 접근
                for i, row in df.iterrows():
                    # 첫번째 열: ID, 세번째 열: 비밀번호
                    if str(row.iloc[0]) == id and str(row.iloc[2]) == pw:
                        st.session_state.login = True
                        st.session_state.name = row.iloc[1]  # 두번째 열: 이름
                        st.session_state.id = id
                        st.rerun()
                st.error("로그인 실패")
            else:
                st.error("데이터를 읽을 수 없습니다")

# 메인
else:
    # 헤더
    col1, col2 = st.columns([3,1])
    with col1:
        st.title(f"👩‍🏫 {st.session_state.name} 선생님")
    with col2:
        if st.button("로그아웃", use_container_width=True):
            st.session_state.login = False
            st.rerun()
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["📋 학생목록", "✅ 출석체크", "📝 진도입력"])
    
    with tab1:
        st.subheader("학생 목록")
        students = read("학생_마스터")
        if not students.empty:
            st.dataframe(students)
        else:
            st.info("학생 데이터가 없습니다")
    
    with tab2:
        st.subheader("출석 체크")
        students = read("학생_마스터")
        if not students.empty:
            for i, row in students.iterrows():
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                with col1:
                    # 두번째 열이 이름
                    name = row.iloc[1] if len(row) > 1 else "이름없음"
                    st.write(f"**{name}**")
                with col2:
                    if st.button("출석", key=f"p{i}"):
                        write("출석_기록", [
                            st.session_state.id,
                            row.iloc[0],  # 학생ID
                            "출석",
                            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        ])
                        st.success("✓")
                with col3:
                    if st.button("지각", key=f"l{i}"):
                        write("출석_기록", [
                            st.session_state.id,
                            row.iloc[0],
                            "지각",
                            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        ])
                        st.warning("△")
                with col4:
                    if st.button("결석", key=f"a{i}"):
                        write("출석_기록", [
                            st.session_state.id,
                            row.iloc[0],
                            "결석",
                            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        ])
                        st.error("✗")
    
    with tab3:
        st.subheader("진도 입력")
        students = read("학생_마스터")
        if not students.empty:
            # 학생 선택
            names = [row.iloc[1] for i, row in students.iterrows() if len(row) > 1]
            selected = st.selectbox("학생 선택", names)
            
            col1, col2 = st.columns(2)
            with col1:
                subject = st.selectbox("과목", ["단어", "문법", "독해"])
                progress = st.text_input("진도")
            with col2:
                rate = st.slider("완료율", 0, 100, 80)
                memo = st.text_area("메모")
            
            if st.button("저장", use_container_width=True):
                # 선택한 학생의 ID 찾기
                student_id = None
                for i, row in students.iterrows():
                    if row.iloc[1] == selected:
                        student_id = row.iloc[0]
                        break
                
                if student_id:
                    write("일일_기록", [
                        st.session_state.id,
                        student_id,
                        subject,
                        progress,
                        f"{rate}%",
                        memo,
                        pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    ])
                    st.success("저장 완료!")
