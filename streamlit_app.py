# streamlit_app.py 예시
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

# 구글 시트 연결
@st.cache_resource
def init_connection():
    # Streamlit secrets에서 인증 정보 가져오기
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(credentials)
    return gc

# 메인 앱
st.title("📚 출석 체크 시스템")

# 학생 선택
student_name = st.selectbox("학생 이름", ["김철수", "이영희", "박민수"])

# 출석 버튼
if st.button("✅ 출석 체크"):
    # 구글 시트에 기록
    gc = init_connection()
    sheet = gc.open("출석부").sheet1
    
    # 현재 시간과 함께 기록
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sheet.append_row([student_name, now, "출석"])
    st.success(f"✅ {student_name} 학생 출석 완료!")
    st.balloons()
