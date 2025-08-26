import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz

# 페이지 설정
st.set_page_config(page_title="학생 진도 관리", layout="wide")

# 스프레드시트 이름 지정
SPREADSHEET_NAME = "학생진도관리"

# Google Sheets 연결 함수
def connect():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(credentials)
    return client

# 시트 초기화 함수
def init_sheets():
    client = connect()
    
    try:
        # 스프레드시트 생성 또는 열기
        try:
            # 이미 존재하는 스프레드시트 열기
            spreadsheet = client.open(SPREADSHEET_NAME)
            st.success(f"'{SPREADSHEET_NAME}' 스프레드시트에 연결했습니다.")
        except gspread.exceptions.SpreadsheetNotFound:
            # 존재하지 않으면 새로 생성
            spreadsheet = client.create(SPREADSHEET_NAME)
            st.success(f"'{SPREADSHEET_NAME}' 스프레드시트를 생성했습니다.")
        
        # 시트 목록 가져오기
        worksheet_names = [ws.title for ws in spreadsheet.worksheets()]
        
        # students 시트 확인/생성
        if "students" not in worksheet_names:
            students_sheet = spreadsheet.add_worksheet(title="students", rows=100, cols=20)
            # 헤더 추가
            students_sheet.update('A1:F1', [['student_id', 'name', 'class_type', 'time', 'class_duration', 'active']])
            st.success("'students' 시트가 생성되었습니다!")
        
        # progress 시트 확인/생성
        if "progress" not in worksheet_names:
            progress_sheet = spreadsheet.add_worksheet(title="progress", rows=100, cols=20)
            # 헤더 추가
            progress_sheet.update('A1:K1', [['student_id', 'date', 'vocabulary', 'listening', 
                                           'grammar_review', 'class_grammar', 'reading', 
                                           'additional', 'feedback', 'homework', 'completed']])
            st.success("'progress' 시트가 생성되었습니다!")
        
        return True
    except Exception as e:
        st.error(f"시트 초기화 중 오류가 발생했습니다: {e}")
        return False

# 데이터 읽기 함수
def read(sheet_name):
    client = connect()
    # 이름으로 스프레드시트 열기
    sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# 데이터 쓰기 함수
def write(sheet_name, data, student_id=None, date=None):
    client = connect()
    sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
    
    if sheet_name == "progress":
        # 특정 학생의 특정 날짜 데이터 업데이트
        records = sheet.get_all_records()
        row_idx = None
        
        for idx, record in enumerate(records):
            if record['student_id'] == student_id and record['date'] == date:
                row_idx = idx + 2  # +2: 헤더 행과 0-인덱스 보정
                break
        
        if row_idx:
            # 기존 레코드 업데이트
            for col, value in data.items():
                col_idx = sheet.find(col).col
                sheet.update_cell(row_idx, col_idx, value)
        else:
            # 새 레코드 추가
            sheet.append_row([
                student_id, 
                date, 
                data.get('vocabulary', ''), 
                data.get('listening', ''), 
                data.get('grammar_review', ''), 
                data.get('class_grammar', ''), 
                data.get('reading', ''), 
                data.get('additional', ''), 
                data.get('feedback', ''), 
                data.get('homework', ''), 
                data.get('completed', False)
            ])

# 현재 날짜 (한국 시간)
def get_kr_today():
    kr_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(kr_tz).strftime('%Y-%m-%d')

# 오늘 요일 (한국 시간)
def get_kr_day():
    kr_tz = pytz.timezone('Asia/Seoul')
    days = ["월", "화", "수", "목", "금", "토", "일"]
    return days[datetime.now(kr_tz).weekday()]

# 학생의 수업일인지 확인하는 함수
def is_class_day(class_type, day):
    if class_type == "월수금" and day in ["월", "수", "금"]:
        return True
    elif class_type == "화목토" and day in ["화", "목", "토"]:
        return True
    return False

# 메인 앱
def main():
    st.title("학생 진도 관리 시스템")
    
    # 첫 실행 시 시트 초기화
    if 'sheets_initialized' not in st.session_state:
        if init_sheets():
            st.session_state.sheets_initialized = True
    
    # 탭 설정
    tab1, tab2, tab3 = st.tabs(["오늘의 수업", "전체 학생 관리", "진도 기록 조회"])
    
    with tab1:
        st.header(f"오늘의 수업 ({get_kr_today()}, {get_kr_day()}요일)")
        
        # 학생 데이터 불러오기
        try:
            students_df = read("students")
            
            # 데이터가 비어있지 않은지 확인
            if not students_df.empty:
                # 오늘 요일에 해당하는 학생만 필터링
                today_day = get_kr_day()
                today_students = students_df[students_df.apply(lambda x: is_class_day(x["class_type"], today_day), axis=1)]
                
                if len(today_students) == 0:
                    st.info(f"오늘({today_day}요일) 수업이 예정된 학생이 없습니다.")
                else:
                    # 학생 목록을 그리드로 표시
                    cols = st.columns(3)
                    for idx, student in today_students.iterrows():
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.write(f"**{student['name']}**")
                            st.write(f"반: {student['class_type']} / 시간: {student['time']}")
                            if st.button(f"진도 관리", key=f"manage_{student['student_id']}"):
                                st.session_state.selected_student = student['student_id']
                                st.session_state.selected_student_name = student['name']
                                st.session_state.selected_date = get_kr_today()
                                st.session_state.view = "student_detail"
                                st.rerun()
            else:
                st.info("등록된 학생이 없습니다. '전체 학생 관리' 탭에서 학생을 추가해 주세요.")
        
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
            st.info("시트 구조를 확인해 주세요. 'students' 시트에는 'student_id', 'name', 'class_type', 'time', 'class_duration', 'active' 열이 있어야 합니다.")
    
    with tab2:
        st.header("전체 학생 관리")
        
        # 새 학생 추가 폼
        with st.expander("새 학생 추가"):
            with st.form("new_student"):
                new_name = st.text_input("학생 이름")
                new_class_type = st.selectbox("반 선택", ["월수금", "화목토"])
                new_time = st.time_input("등원 시간")
                new_duration = st.number_input("수업 시간 (분)", min_value=30, max_value=180, step=30)
                
                if st.form_submit_button("학생 추가"):
                    try:
                        # 스프레드시트에 연결
                        client = connect()
                        sheet = client.open(SPREADSHEET_NAME).worksheet("students")
                        
                        # 기존 학생 데이터 가져오기
                        existing_data = sheet.get_all_records()
                        
                        # 새 학생 ID 생성
                        new_id = f"{len(existing_data) + 1:03d}"
                        
                        # Google Sheets에 추가
                        sheet.append_row([
                            new_id, 
                            new_name, 
                            new_class_type, 
                            new_time.strftime("%H:%M"), 
                            new_duration,
                            True
                        ])
                        st.success(f"{new_name} 학생이 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"학생 추가 중 오류가 발생했습니다: {e}")
        
        # 학생 목록 표시
        try:
            students_df = read("students")
            if students_df.empty:
                st.info("등록된 학생이 없습니다.")
            else:
                st.subheader("학생 목록")
                # 반별로 정렬
                students_df = students_df.sort_values(by=['class_type', 'time'])
                
                # 월수금반과 화목토반 구분
                st.write("### 월수금반")
                msf_students = students_df[students_df['class_type'] == '월수금']
                for idx, student in msf_students.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{student['name']}** - {student['time']}")
                    with col2:
                        if st.button("진도 관리", key=f"progress_msf_{student['student_id']}"):
                            st.session_state.selected_student = student['student_id']
                            st.session_state.selected_student_name = student['name']
                            st.session_state.selected_date = get_kr_today()
                            st.session_state.view = "student_detail"
                            st.rerun()
                
                st.write("### 화목토반")
                tts_students = students_df[students_df['class_type'] == '화목토']
                for idx, student in tts_students.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{student['name']}** - {student['time']}")
                    with col2:
                        if st.button("진도 관리", key=f"progress_tts_{student['student_id']}"):
                            st.session_state.selected_student = student['student_id']
                            st.session_state.selected_student_name = student['name']
                            st.session_state.selected_date = get_kr_today()
                            st.session_state.view = "student_detail"
                            st.rerun()
        
        except Exception as e:
            st.error(f"학생 목록을 불러오는 중 오류가 발생했습니다: {e}")
    
    # 진도 기록 조회 탭
    with tab3:
        st.header("진도 기록 조회")
        
        try:
            # 학생 목록 가져오기
            students_df = read("students")
            if students_df.empty:
                st.info("등록된 학생이 없습니다.")
            else:
                # 학생 선택
                student_names = students_df['name'].tolist()
                selected_student_name = st.selectbox("학생 선택", student_names)
                
                # 선택된 학생의 ID 가져오기
                selected_student = students_df[students_df['name'] == selected_student_name].iloc[0]
                student_id = selected_student['student_id']
                
                # 날짜 범위 선택
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("시작일", 
                                              value=datetime.strptime(get_kr_today(), '%Y-%m-%d') - timedelta(days=30))
                with col2:
                    end_date = st.date_input("종료일", 
                                            value=datetime.strptime(get_kr_today(), '%Y-%m-%d'))
                
                # 조회 버튼
                if st.button("진도 기록 조회"):
                    # 진도 데이터 가져오기
                    progress_df = read("progress")
                    
                    # 선택된 학생의 지정된 날짜 범위 내 진도 기록 필터링
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    student_progress = progress_df[
                        (progress_df["student_id"] == student_id) & 
                        (progress_df["date"] >= start_date_str) & 
                        (progress_df["date"] <= end_date_str)
                    ]
                    
                    if student_progress.empty:
                        st.info(f"{selected_student_name} 학생의 선택된 기간 내 진도 기록이 없습니다.")
                    else:
                        # 날짜별로 정렬
                        student_progress = student_progress.sort_values(by='date', ascending=False)
                        
                        # 진도 기록 표시
                        for _, progress in student_progress.iterrows():
                            with st.expander(f"{progress['date']} 진도 기록"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**단어**")
                                    st.write(progress['vocabulary'])
                                    
                                    st.write("**듣기**")
                                    st.write(progress['listening'])
                                    
                                    st.write("**관리 문법**")
                                    st.write(progress['grammar_review'])
                                    
                                    st.write("**수업 문법**")
                                    st.write(progress['class_grammar'])
                                
                                with col2:
                                    st.write("**독해**")
                                    st.write(progress['reading'])
                                    
                                    st.write("**추가 학습**")
                                    st.write(progress['additional'])
                                    
                                    st.write("**일일 피드백**")
                                    st.write(progress['feedback'])
                                    
                                    st.write("**숙제**")
                                    st.write(progress['homework'])
                                
                                st.write(f"**완료 여부**: {'완료' if progress['completed'] else '미완료'}")
        
        except Exception as e:
            st.error(f"진도 기록을 불러오는 중 오류가 발생했습니다: {e}")
    
    # 학생 상세 페이지 뷰
    if "view" in st.session_state and st.session_state.view == "student_detail":
        st.title(f"{st.session_state.selected_student_name} 학생 진도 관리")
        st.subheader(f"날짜: {st.session_state.selected_date}")
        
        # 날짜 선택기
        new_date = st.date_input("다른 날짜 선택", 
                                value=datetime.strptime(st.session_state.selected_date, "%Y-%m-%d"))
        st.session_state.selected_date = new_date.strftime('%Y-%m-%d')
        
        # 진도 데이터 불러오기
        try:
            progress_df = read("progress")
            student_progress = progress_df[
                (progress_df["student_id"] == st.session_state.selected_student) & 
                (progress_df["date"] == st.session_state.selected_date)
            ]
            
            # 진도 입력 폼
            with st.form("progress_form"):
                vocabulary = st.text_area("단어", 
                                         value=student_progress["vocabulary"].values[0] if not student_progress.empty else "")
                listening = st.text_area("듣기", 
                                        value=student_progress["listening"].values[0] if not student_progress.empty else "")
                grammar_review = st.text_area("관리 문법", 
                                             value=student_progress["grammar_review"].values[0] if not student_progress.empty else "")
                class_grammar = st.text_area("수업 문법", 
                                            value=student_progress["class_grammar"].values[0] if not student_progress.empty else "")
                reading = st.text_area("독해", 
                                      value=student_progress["reading"].values[0] if not student_progress.empty else "")
                additional = st.text_area("추가 학습", 
                                         value=student_progress["additional"].values[0] if not student_progress.empty else "")
                feedback = st.text_area("일일 피드백", 
                                       value=student_progress["feedback"].values[0] if not student_progress.empty else "")
                homework = st.text_area("숙제", 
                                       value=student_progress["homework"].values[0] if not student_progress.empty else "")
                completed = st.checkbox("완료", 
                                       value=student_progress["completed"].values[0] if not student_progress.empty else False)
                
                if st.form_submit_button("저장"):
                    progress_data = {
                        'vocabulary': vocabulary,
                        'listening': listening,
                        'grammar_review': grammar_review,
                        'class_grammar': class_grammar,
                        'reading': reading,
                        'additional': additional,
                        'feedback': feedback,
                        'homework': homework,
                        'completed': completed
                    }
                    
                    write("progress", progress_data, 
                         student_id=st.session_state.selected_student, 
                         date=st.session_state.selected_date)
                    
                    st.success("진도 정보가 저장되었습니다!")
            
            # 이전 진도 기록 표시
            if not student_progress.empty:
                with st.expander("저장된 진도 기록"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**단어**")
                        st.write(student_progress["vocabulary"].values[0])
                        
                        st.write("**듣기**")
                        st.write(student_progress["listening"].values[0])
                        
                        st.write("**관리 문법**")
                        st.write(student_progress["grammar_review"].values[0])
                        
                        st.write("**수업 문법**")
                        st.write(student_progress["class_grammar"].values[0])
                    
                    with col2:
                        st.write("**독해**")
                        st.write(student_progress["reading"].values[0])
                        
                        st.write("**추가 학습**")
                        st.write(student_progress["additional"].values[0])
                        
                        st.write("**일일 피드백**")
                        st.write(student_progress["feedback"].values[0])
                        
                        st.write("**숙제**")
                        st.write(student_progress["homework"].values[0])
                    
                    st.write(f"**완료 여부**: {'완료' if student_progress['completed'].values[0] else '미완료'}")
            
            # 뒤로 가기 버튼
            if st.button("뒤로 가기"):
                st.session_state.pop("view", None)
                st.session_state.pop("selected_student", None)
                st.session_state.pop("selected_student_name", None)
                st.session_state.pop("selected_date", None)
                st.rerun()
        
        except Exception as e:
            st.error(f"진도 데이터를 불러오는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
