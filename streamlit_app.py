import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def connect_to_gsheet():
    """구글 시트에 연결하는 함수"""
    # 서비스 계정 정보 불러오기
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    
    # 구글 시트 클라이언트 생성
    client = gspread.authorize(credentials)
    
    # 스프레드시트 열기
    sheet_id = "1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y"
    sheet = client.open_by_key(sheet_id)
    
    return sheet

def read(worksheet_name="Sheet1"):
    """지정된 워크시트에서 데이터 읽기"""
    sheet = connect_to_gsheet()
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def write(df, worksheet_name="Sheet1"):
    """데이터프레임을 지정된 워크시트에 쓰기"""
    sheet = connect_to_gsheet()
    worksheet = sheet.worksheet(worksheet_name)
    
    # 기존 데이터 지우기
    worksheet.clear()
    
    # 헤더 쓰기
    worksheet.append_row(df.columns.tolist())
    
    # 데이터 쓰기
    worksheet.append_rows(df.values.tolist())
    
    return True

# Streamlit 앱 시작
st.title("Google Sheets 연동 테스트")

# 데이터 가져오기 버튼
if st.button("데이터 가져오기"):
    try:
        df = read()
        st.success("구글 시트에서 데이터를 성공적으로 가져왔습니다!")
        st.write(df)
    except Exception as e:
        st.error(f"데이터 가져오기 오류: {e}")

# 간단한 데이터 작성 테스트
st.subheader("데이터 추가 테스트")
with st.form("data_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름")
    with col2:
        score = st.number_input("점수", min_value=0, max_value=100)
    
    submit = st.form_submit_button("데이터 추가")
    
    if submit and name:
        try:
            # 기존 데이터 가져오기
            df = read()
            
            # 새 데이터 추가
            new_data = pd.DataFrame({"이름": [name], "점수": [score]})
            updated_df = pd.concat([df, new_data], ignore_index=True)
            
            # 업데이트된 데이터 쓰기
            write(updated_df)
            
            st.success("데이터가 성공적으로 추가되었습니다!")
            st.write(updated_df)
        except Exception as e:
            st.error(f"데이터 추가 오류: {e}")
