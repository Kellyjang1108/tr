import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="학생관리", page_icon="📚")

# 초기화
if 'login' not in st.session_state:
    st.session_state.login = False

# 구글시트 연결
@st.cache_resource
def connect():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        return client.open_by_key("1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y")
    except:
        return None

# 시트 읽기
def read(sheet_name):
    try:
        sheet = connect()
        data = sheet.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# 시트 쓰기
def write(sheet_name, row):
    try:
        sheet = connect()
        sheet.worksheet(sheet_name).append_row(row)
        return True
    except:
        return False

# 로그인
if not st.session_state.login:
    st.title("로그인")
    id = st.text_input("ID")
    pw = st.text_input("PW", type="password")
    
    if st.button("로그인"):
        df = read("강사_마스터")
        if not df.empty:
            # 첫번째 컬럼을 ID, 세번째를 PW로 사용
            if len(df.columns) >= 3:
                check = df[(df.iloc[:,0].astype(str)==id) & (df.iloc[:,2].astype(str)==pw)]
                if not check.empty:
                    st.session_state.login = True
                    st.session_state.name = check.iloc[0,1]  # 두번째 컬럼이 이름
                    st.rerun()
        st.error("실패")

# 메인
else:
    st.title(f"{st.session_state.name}님")
    
    if st.button("로그아웃"):
        st.session_state.login = False
        st.rerun()
    
    tab1, tab2 = st.tabs(["학생", "출석"])
    
    with tab1:
        students = read("학생_마스터")
        st.dataframe(students)
    
    with tab2:
        students = read("학생_마스터")
        if not students.empty:
            for i, row in students.iterrows():
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(row.iloc[1] if len(row) > 1 else "이름없음")
                with c2:
                    if st.button("출석", key=f"a{i}"):
                        write("출석_기록", ["오늘", row.iloc[0], "출석"])
                        st.success("✓")
                with c3:
                    if st.button("결석", key=f"b{i}"):
                        write("출석_기록", ["오늘", row.iloc[0], "결석"])
                        st.error("✗")
