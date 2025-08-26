import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.title("Google Sheets 연결 테스트")

# Google Sheets 연결 함수
def connect():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(credentials)
        st.success("Google API 인증 성공!")
        return client
    except Exception as e:
        st.error(f"Google API 인증 오류: {e}")
        return None

# 스프레드시트 연결 테스트
if st.button("스프레드시트 연결 테스트"):
    client = connect()
    if client:
        try:
            spreadsheet_id = st.secrets["general"]["spreadsheet_id"]
            sheet = client.open_by_key(spreadsheet_id)
            st.success(f"스프레드시트 '{sheet.title}'에 연결 성공!")
            
            # 시트 목록 표시
            st.write("시트 목록:")
            for worksheet in sheet.worksheets():
                st.write(f"- {worksheet.title}")
        except Exception as e:
            st.error(f"스프레드시트 연결 오류: {e}")
