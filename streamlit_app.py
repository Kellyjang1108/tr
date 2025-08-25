import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("연동 테스트")

# 1. 서비스 계정 확인
try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    st.success("✅ 서비스 계정 인증 성공")
except Exception as e:
    st.error(f"❌ 서비스 계정 오류: {e}")
    st.stop()

# 2. gspread 연결
try:
    client = gspread.authorize(creds)
    st.success("✅ gspread 연결 성공")
except Exception as e:
    st.error(f"❌ gspread 오류: {e}")
    st.stop()

# 3. 시트 열기
try:
    sheet = client.open_by_key("1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y")
    st.success("✅ 시트 열기 성공")
    
    # 4. 워크시트 목록
    worksheets = sheet.worksheets()
    st.write("시트 탭 목록:", [ws.title for ws in worksheets])
    
    # 5. 데이터 읽기
    if "강사_마스터" in [ws.title for ws in worksheets]:
        data = sheet.worksheet("강사_마스터").get_all_records()
        st.write("강사_마스터 데이터:", data)
    else:
        st.warning("강사_마스터 시트가 없습니다")
        
except Exception as e:
    st.error(f"❌ 시트 열기 오류: {e}")
