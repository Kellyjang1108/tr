# 필요한 라이브러리들을 불러옵니다.
import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# Streamlit 앱의 제목을 설정합니다.
st.set_page_config(
    page_title="학생 진도 관리",
    page_icon="📚",
    layout="wide"
)

def run_app():
    """메인 앱 실행 함수입니다."""
    
    # --------------------
    # 1. 구글 시트 연동
    # --------------------
    # secrets.toml 파일에 있는 서비스 계정 정보를 불러와 인증합니다.
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # secrets.toml에 있는 시트 ID를 사용해 스프레드시트를 엽니다.
        # 시트 ID는 secrets.toml에 "sheet_id = '시트ID'" 형식으로 저장되어야 합니다.
        spreadsheet = gc.open_by_key(st.secrets["sheet_id"])
        worksheet = spreadsheet.sheet1
        
        # 시트의 모든 데이터를 pandas DataFrame으로 불러옵니다.
        # 이 데이터는 한 번만 불러오고, 이후에는 캐시하여 성능을 높입니다.
        @st.cache_data(ttl=60)
        def get_dataframe():
            data = worksheet.get_all_records()
            return pd.DataFrame(data)

        # 데이터프레임 불러오기
        df = get_dataframe()
    except Exception as e:
        st.error(f"구글 시트 연동 오류: {e}")
        st.info("secrets.toml 파일의 서비스 계정 정보와 시트 ID가 올바른지 확인해주세요. 특히 'sheet_id'가 정확히 설정되었는지 확인하세요.")
        st.stop()
        
    # --------------------
    # 2. UI 구성
    # --------------------
    st.title('학생 진도 관리 시스템')
    st.markdown('---')
    
    # 사이드바에 학생 선택 메뉴를 만듭니다.
    student_names = df['이름'].tolist()
    selected_name = st.sidebar.selectbox('학생을 선택하세요', student_names)
    
    # --------------------
    # 3. 학생 정보 표시
    # --------------------
    # 선택된 학생의 데이터를 가져옵니다.
    selected_student = df[df['이름'] == selected_name].iloc[0]
    
    st.header(f"📚 {selected_student['이름']} 학생")
    st.subheader(f"🗓️ 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
    st.subheader(f"⏰ 수업 시간: {selected_student['수업 시간']}")

    st.markdown("### 오늘 할 진도")
    st.info(selected_student['오늘 진도'])
    
    # --------------------
    # 4. 진도 기록 및 저장
    # --------------------
    # 진도를 기록할 텍스트 에어리어와 저장 버튼을 만듭니다.
    st.markdown("---")
    st.subheader("📝 오늘 끝낸 진도 기록하기")
    progress_text = st.text_area(
        "오늘 완료한 진도 내용을 여기에 기록하세요.",
        value=selected_student.get('완료 진도', ''),
        height=150
    )
    
    if st.button('✨ 기록 저장'):
        with st.spinner('진도 기록 중...'):
            try:
                # 선택된 학생의 행 인덱스를 찾습니다.
                row_index = df[df['이름'] == selected_name].index[0] + 2 # 1-based index + header row
                
                # '완료 진도' 컬럼의 위치를 찾습니다.
                progress_col_index = df.columns.get_loc('완료 진도') + 1 # 1-based index
                
                # 구글 시트의 해당 셀에 새로운 진도 내용을 업데이트합니다.
                worksheet.update_cell(row_index, progress_col_index, progress_text)
                
                st.success(f"'{selected_name}' 학생의 진도가 성공적으로 저장되었습니다!")
                # 데이터 캐시를 지워서 새로고침 시 업데이트된 내용이 보이도록 합니다.
                get_dataframe.clear()
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")
                st.info("Google Sheets의 '이름', '수업 시간', '오늘 진도', '완료 진도' 컬럼명이 정확한지 확인해주세요.")

# 앱을 실행합니다.
if __name__ == "__main__":
    run_app()
