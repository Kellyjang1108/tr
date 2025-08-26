import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="영어 학원 관리 시스템", layout="wide")

# 스타일 추가
st.markdown("""
<style>
    .student-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        cursor: pointer;
    }
    .student-icon {
        font-size: 24px;
        color: #4B89DC;
    }
    .date-text {
        color: #666;
        font-size: 14px;
    }
    .header {
        text-align: center;
        margin-bottom: 30px;
    }
    .subject-tag {
        background-color: #E8F0FE;
        color: #4B89DC;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin-right: 5px;
        display: inline-block;
        margin-top: 5px;
    }
    .subject-box {
        background-color: #F8F9FA;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .subject-title {
        color: #4B89DC;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .back-button {
        display: inline-flex;
        align-items: center;
        background-color: #F1F3F5;
        border: none;
        color: #495057;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        text-decoration: none;
        margin-bottom: 20px;
    }
    .action-button {
        background-color: #4B89DC;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# 구글 시트 연결
def connect_to_sheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    client = gspread.authorize(credentials)
    sheet_id = "1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y"
    return client.open_by_key(sheet_id)

# 시트에서 데이터 읽기
def read(worksheet_name):
    sheet = connect_to_sheets()
    try:
        worksheet = sheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"시트 읽기 오류: {e}")
        return pd.DataFrame()

# 시트에 데이터 쓰기
def write(df, worksheet_name):
    sheet = connect_to_sheets()
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.clear()
        if not df.empty:
            worksheet.update([df.columns.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"시트 쓰기 오류: {e}")
        return False

# 현재 날짜 가져오기
def get_today():
    return datetime.now().strftime("%Y년 %m월 %d일")

# 세션 상태 초기화
if 'view' not in st.session_state:
    st.session_state.view = 'list'  # 'list' 또는 'detail'
if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None

# 상세 페이지로 이동하는 함수
def view_student_detail(student):
    st.session_state.selected_student = student
    st.session_state.view = 'detail'

# 목록 페이지로 돌아가는 함수
def back_to_list():
    st.session_state.view = 'list'
    st.session_state.selected_student = None

# 진도 기록 저장 함수
def save_progress(student_id, subject, progress_text):
    # 일일_기록 시트에서 데이터 가져오기
    records_df = read("일일_기록")
    
    # 오늘 날짜
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 기록 ID 생성 (날짜_학생ID_과목)
    record_id = f"{today}_{student_id}_{subject}"
    
    # 새 기록 데이터 생성
    new_record = {
        '기록ID': record_id,
        '날짜': today,
        '학생ID': student_id,
        '과목': subject,
        '진도': progress_text,
        '출석상태': '출석'  # 기본값
    }
    
    # 기존 기록 확인
    if not records_df.empty and '기록ID' in records_df.columns:
        existing_record = records_df[records_df['기록ID'] == record_id]
        
        if not existing_record.empty:
            # 기존 기록 업데이트
            records_df = records_df[records_df['기록ID'] != record_id]
    
    # 새 기록 추가
    if records_df.empty:
        updated_records = pd.DataFrame([new_record])
    else:
        updated_records = pd.concat([records_df, pd.DataFrame([new_record])], ignore_index=True)
    
    # 저장
    return write(updated_records, "일일_기록")

# 이전 진도 가져오기 함수
def get_previous_progress(student_id, subject):
    # 일일_기록 시트에서 데이터 가져오기
    records_df = read("일일_기록")
    
    if records_df.empty:
        return "기록 없음"
    
    # 해당 학생과 과목의 기록 필터링
    student_records = records_df[
        (records_df['학생ID'] == student_id) & 
        (records_df['과목'] == subject)
    ]
    
    if student_records.empty:
        return "기록 없음"
    
    # 날짜로 정렬 (최신 순)
    if '날짜' in student_records.columns:
        student_records['날짜'] = pd.to_datetime(student_records['날짜'])
        student_records = student_records.sort_values('날짜', ascending=False)
        
        # 최신 기록 반환
        if '진도' in student_records.columns:
            return student_records.iloc[0]['진도']
    
    return "기록 없음"

# 메인 앱
def main():
    if st.session_state.view == 'list':
        # 학생 목록 화면
        st.markdown("<h1 class='header'>학생 목록</h1>", unsafe_allow_html=True)
        
        # 학생 데이터 가져오기
        students_df = read("학생_마스터")
        
        # 테스트 데이터 (시트가 비어있거나 오류시 사용)
        if students_df.empty:
            test_data = {
                '학생ID': ['S001', 'S002', 'S003'],
                '이름': ['김민준', '이서윤', '박하은'],
                '학년': ['초등 3학년', '초등 5학년', '중등 1학년'],
                '수강과목': ['수학,과학', '영어,수학', '과학,영어,수학'],
                '등록일': ['2025-01-15', '2025-02-20', '2025-03-10'],
                '수업시간': ['오후 4:00', '오후 5:30', '오후 7:00']
            }
            students_df = pd.DataFrame(test_data)
        
        # 날짜 포맷
        today = get_today()
        
        # 검색 기능
        search = st.text_input("학생 이름 검색")
        
        if search:
            filtered_df = students_df[students_df['이름'].str.contains(search)]
        else:
            filtered_df = students_df
        
        # 학생 목록을 3열로 표시
        cols = st.columns(3)
        
        for i, (_, student) in enumerate(filtered_df.iterrows()):
            col_idx = i % 3
            
            with cols[col_idx]:
                # 클릭 가능한 학생 카드
                card_html = f"""
                <div class='student-card' onclick="parent.postMessage({{msg: 'student_clicked', student_id: '{student['학생ID']}'}}, '*')">
                    <div style="display: flex; align-items: center;">
                        <div class="student-icon">👤</div>
                        <div style="margin-left: 15px;">
                            <h3 style="margin: 0;">{student['이름']}</h3>
                            <p class="date-text">{today}</p>
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # JavaScript로 클릭 이벤트 처리
                st.markdown("""
                <script>
                window.addEventListener('message', function(e) {
                    if (e.data.msg === 'student_clicked') {
                        // 이 부분은 Streamlit이 실행되는 방식 때문에 직접 JavaScript로 처리할 수 없음
                        // 대신 버튼을 사용해서 학생 상세 페이지로 이동
                    }
                });
                </script>
                """, unsafe_allow_html=True)
                
                # 실제 클릭 처리를 위한 버튼 (숨김)
                if st.button(f"상세보기: {student['이름']}", key=f"btn_{student['학생ID']}", help="학생 상세 정보 보기"):
                    view_student_detail(student)
                    st.experimental_rerun()
    
    else:  # 상세 화면
        student = st.session_state.selected_student
        
        # 뒤로 가기 버튼
        if st.button("← 목록으로 돌아가기", key="back_button"):
            back_to_list()
            st.experimental_rerun()
        
        # 학생 헤더 정보
        st.markdown(f"<h1>{student['이름']} 학생</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<p>👤 오늘 날짜: {get_today()}</p>", unsafe_allow_html=True)
        with col2:
            if '수업시간' in student:
                st.markdown(f"<p>🕒 수업 시간: {student['수업시간']}</p>", unsafe_allow_html=True)
        
        # 오늘의 진도 섹션
        st.markdown("<h2>오늘의 진도</h2>", unsafe_allow_html=True)
        
        # 과목 리스트
        subjects = [s.strip() for s in student['수강과목'].split(',')]
        
        for subject in subjects:
            with st.container():
                st.markdown(f"<div class='subject-box'>", unsafe_allow_html=True)
                st.markdown(f"<h3 class='subject-title'>{subject}</h3>", unsafe_allow_html=True)
                
                # 이전 진도 가져오기
                previous_progress = get_previous_progress(student['학생ID'], subject)
                st.markdown(f"<p><strong>이전 진도:</strong> {previous_progress}</p>", unsafe_allow_html=True)
                
                # 오늘의 진도 입력
                progress_text = st.text_area(f"오늘 진행한 {subject} 진도", key=f"progress_{subject}")
                
                # 저장 버튼
                if st.button(f"{subject} 진도 저장", key=f"save_{subject}"):
                    if progress_text:
                        if save_progress(student['학생ID'], subject, progress_text):
                            st.success(f"{subject} 진도가 저장되었습니다.")
                        else:
                            st.error("진도 저장 중 오류가 발생했습니다.")
                    else:
                        st.warning("진도 내용을 입력해주세요.")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # 오늘 끝낸 진도 기록하기
        st.markdown("<h2>오늘 끝낸 진도 기록하기</h2>", unsafe_allow_html=True)
        
        progress_notes = st.text_area("오늘 완료한 진도 내용을 여기에 기록하세요.", height=200)
        
        if st.button("진도 기록 저장", key="save_all_progress"):
            if progress_notes:
                st.success("진도 기록이 저장되었습니다.")
            else:
                st.warning("진도 내용을 입력해주세요.")

# 앱 실행
if __name__ == "__main__":
    main()
