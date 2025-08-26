import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# 구글 시트 연결 함수
def connect_to_gsheet():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    client = gspread.authorize(credentials)
    sheet_id = "1YfyKfMv20uDYaXilc-dTlvaueR85Z5Bn-z9uiN9AO5Y"
    sheet = client.open_by_key(sheet_id)
    return sheet

# 시트에서 데이터 읽기
def read(worksheet_name):
    sheet = connect_to_gsheet()
    try:
        worksheet = sheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"시트 읽기 오류: {e}")
        return pd.DataFrame()

# 시트에 데이터 쓰기
def write(df, worksheet_name):
    sheet = connect_to_gsheet()
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.clear()
        if len(df) > 0:  # 데이터가 있는 경우만 처리
            worksheet.update([df.columns.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"시트 쓰기 오류: {e}")
        return False

# 시트에 새 행 추가
def append_row(row_data, worksheet_name):
    sheet = connect_to_gsheet()
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"행 추가 오류: {e}")
        return False

# 로그인 함수
def login(username, password):
    teachers_df = read("강사_마스터")
    if teachers_df.empty:
        return None
    
    teacher = teachers_df[(teachers_df["이름"] == username) & (teachers_df["비밀번호"] == password)]
    if not teacher.empty:
        return teacher.iloc[0].to_dict()
    return None

# 오늘 날짜 가져오기
def get_today():
    return datetime.now().strftime("%Y-%m-%d")

# Streamlit 앱 시작
st.title("영어 학원 관리 시스템")

# 세션 상태 초기화
if "login" not in st.session_state:
    st.session_state.login = None

# 로그인 상태 확인
if not st.session_state.login:
    # 로그인 폼
    with st.form("login_form"):
        st.subheader("강사 로그인")
        username = st.text_input("이름")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")
        
        if submit:
            teacher = login(username, password)
            if teacher:
                st.session_state.login = teacher
                st.success("로그인 성공!")
                st.experimental_rerun()
            else:
                st.error("로그인 정보가 일치하지 않습니다.")
else:
    # 로그인 상태 - 메인 화면
    teacher = st.session_state.login
    st.write(f"안녕하세요, {teacher['이름']} 선생님!")
    
    if st.button("로그아웃"):
        st.session_state.login = None
        st.experimental_rerun()
    
    # 학생 목록 가져오기
    students_df = read("학생_마스터")
    teacher_students = students_df[students_df["담당강사ID"] == teacher["강사ID"]]
    
    if teacher_students.empty:
        st.warning("담당 학생이 없습니다.")
    else:
        # 탭 생성
        tab1, tab2 = st.tabs(["오늘의 수업", "기록 조회"])
        
        with tab1:
            st.subheader("오늘의 수업")
            today = get_today()
            
            # 일일 기록 가져오기
            records_df = read("일일_기록")
            
            # 학생별 과목 및 시간 목록 표시
            for _, student in teacher_students.iterrows():
                st.markdown(f"### {student['이름']}")
                
                # 학생의 과목 목록
                subjects = student['수강과목'].split(',')
                
                for subject in subjects:
                    subject = subject.strip()
                    st.markdown(f"#### 과목: {subject}")
                    
                    # 이전 진도 확인
                    previous_records = records_df[
                        (records_df['학생ID'] == student['학생ID']) & 
                        (records_df['과목'] == subject)
                    ]
                    
                    last_progress = "없음"
                    next_progress = "없음"
                    
                    if not previous_records.empty:
                        # 날짜 기준 정렬
                        previous_records['날짜'] = pd.to_datetime(previous_records['날짜'])
                        previous_records = previous_records.sort_values('날짜', ascending=False)
                        
                        if not previous_records.empty:
                            last_record = previous_records.iloc[0]
                            last_progress = last_record.get('진도', '없음')
                            next_progress = last_record.get('다음진도계획', '없음')
                    
                    # 정보 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**이전 수업 정보**")
                        st.markdown(f"마지막 진도: {last_progress}")
                        st.markdown(f"다음 진도 계획: {next_progress}")
                    
                    # 출석 및 진도 기록 입력 폼
                    with col2:
                        with st.form(key=f"record_form_{student['학생ID']}_{subject}"):
                            st.markdown("**오늘 수업 기록**")
                            
                            # 출석 상태
                            attendance = st.selectbox(
                                "출석 상태",
                                options=["출석", "지각", "결석"],
                                key=f"att_{student['학생ID']}_{subject}"
                            )
                            
                            # 결석 사유 (결석인 경우만)
                            absence_reason = ""
                            if attendance == "결석":
                                absence_reason = st.selectbox(
                                    "결석 사유",
                                    options=["질병", "가족행사", "학교행사", "기타"],
                                    key=f"reason_{student['학생ID']}_{subject}"
                                )
                            
                            # 진도 입력
                            progress = st.text_area(
                                "오늘 진행한 진도",
                                key=f"prog_{student['학생ID']}_{subject}"
                            )
                            
                            # 다음 진도 계획
                            next_plan = st.text_area(
                                "다음 진도 계획",
                                key=f"next_{student['학생ID']}_{subject}"
                            )
                            
                            # 특이사항
                            notes = st.text_area(
                                "특이사항",
                                key=f"note_{student['학생ID']}_{subject}"
                            )
                            
                            # 저장 버튼
                            submit_button = st.form_submit_button("저장")
                            
                            if submit_button:
                                # 기록 데이터 생성
                                record_data = {
                                    "기록ID": f"{today}_{student['학생ID']}_{subject}",
                                    "날짜": today,
                                    "학생ID": student['학생ID'],
                                    "강사ID": teacher['강사ID'],
                                    "과목": subject,
                                    "출석상태": attendance,
                                    "결석사유": absence_reason,
                                    "진도": progress,
                                    "다음진도계획": next_plan,
                                    "특이사항": notes
                                }
                                
                                # 기존 기록이 있는지 확인
                                existing_record = records_df[records_df["기록ID"] == record_data["기록ID"]]
                                
                                if existing_record.empty:
                                    # 새 기록 추가
                                    new_record_df = pd.DataFrame([record_data])
                                    updated_records = pd.concat([records_df, new_record_df], ignore_index=True)
                                else:
                                    # 기존 기록 업데이트
                                    records_df = records_df[records_df["기록ID"] != record_data["기록ID"]]
                                    new_record_df = pd.DataFrame([record_data])
                                    updated_records = pd.concat([records_df, new_record_df], ignore_index=True)
                                
                                # 저장
                                if write(updated_records, "일일_기록"):
                                    st.success(f"{student['이름']}의 {subject} 기록이 저장되었습니다.")
                                else:
                                    st.error("기록 저장 중 오류가 발생했습니다.")
                    
                    st.markdown("---")
        
        with tab2:
            st.subheader("기록 조회")
            
            # 학생 선택
            selected_student = st.selectbox(
                "학생 선택",
                options=teacher_students["이름"].tolist()
            )
            
            if selected_student:
                student_info = teacher_students[teacher_students["이름"] == selected_student].iloc[0]
                
                # 과목 선택
                subjects = [s.strip() for s in student_info["수강과목"].split(",")]
                selected_subject = st.selectbox("과목 선택", options=subjects)
                
                if selected_subject:
                    # 선택한 학생/과목의 기록 조회
                    records_df = read("일일_기록")
                    student_records = records_df[
                        (records_df["학생ID"] == student_info["학생ID"]) & 
                        (records_df["과목"] == selected_subject)
                    ]
                    
                    if student_records.empty:
                        st.info(f"{selected_student}의 {selected_subject} 과목 기록이 없습니다.")
                    else:
                        # 날짜로 정렬
                        student_records["날짜"] = pd.to_datetime(student_records["날짜"])
                        student_records = student_records.sort_values("날짜", ascending=False)
                        
                        # 기록 표시
                        for _, record in student_records.iterrows():
                            with st.expander(f"{record['날짜'].strftime('%Y-%m-%d')} 수업"):
                                st.write(f"**출석 상태:** {record['출석상태']}")
                                if record['출석상태'] == "결석" and record['결석사유']:
                                    st.write(f"**결석 사유:** {record['결석사유']}")
                                st.write(f"**진행한 진도:** {record['진도']}")
                                st.write(f"**다음 진도 계획:** {record['다음진도계획']}")
                                if record['특이사항']:
                                    st.write(f"**특이사항:** {record['특이사항']}")
