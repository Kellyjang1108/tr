import streamlit as st

st.title("테스트 앱")
st.write("이 앱이 실행되나요?")

# 시크릿 확인
if "general" in st.secrets:
    st.success("시크릿 설정이 존재합니다!")
    st.write(f"스프레드시트 ID: {st.secrets['general']['spreadsheet_id']}")
else:
    st.error("시크릿 설정이 없습니다!")

# 서비스 계정 확인
if "gcp_service_account" in st.secrets:
    st.success("서비스 계정 정보가 존재합니다!")
    # 이메일만 안전하게 표시
    if "client_email" in st.secrets["gcp_service_account"]:
        st.write(f"서비스 계정 이메일: {st.secrets['gcp_service_account']['client_email']}")
else:
    st.error("서비스 계정 정보가 없습니다!")
