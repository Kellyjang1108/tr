import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def connect_to_gsheet():
    """구글 시트에 연결하는 함수"""
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

def read(worksheet_name):
    """지정된 워크시트에서 데이터 읽기"""
    sheet = connect_to_gsheet()
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def write(df, worksheet_name):
    """데이터프레임을 지정된 워크시트에 쓰기"""
    sheet = connect_to_gsheet()
    worksheet = sheet.worksheet(worksheet_name)
    
    # 기존 데이터 지우기
    worksheet.clear()
    
    # 헤더 쓰기
    worksheet.append_row(df.columns.tolist())
    
    # 데이터 쓰기
    if not df.empty:
        worksheet.append_rows(df.values.tolist())
    
    return True

def append(row_data, worksheet_name):
    """새 행을 워크시트에 추가"""
    sheet = connect_to_gsheet()
    worksheet = sheet.worksheet(worksheet_name)
    worksheet.append_row(row_data)
    return True

def get_teacher_by_credentials(email, password):
    """강사 로그인 검증"""
    teachers_df = read("강사_마스터")
    teacher = teachers_df[(teachers_df['이메일'] == email) & (teachers_df['비밀번호'] == password)]
    if not teacher.empty:
        return teacher.iloc[0].to_dict()
    return None

def get_students_for_teacher(teacher_id):
    """강사 담당 학생 목록 가져오기"""
    students_df = read("학생_마스터")
    return students_df[students_df['담당강사ID'] == teacher_id]

def get_today_classes(teacher_id):
    """오늘 수업할 학생 및 과목 정보 가져오기"""
    today = datetime.now(KST).strftime('%Y-%m-%d')
    students_df = get_students_for_teacher(teacher_id)
    
    today_classes = []
    
    for _, student in students_df.iterrows():
        subjects = student['수강과목'].split(',')
        for subject in subjects:
            subject = subject.strip()
            today_classes.append({
                '학생ID': student['학생ID'],
                '학생이름': student['이름'],
                '과목': subject,
                '날짜': today
            })
    
    return pd.DataFrame(today_classes)

def get_previous_progress(student_id, subject):
    """특정 학생의 특정 과목 이전 진도 정보 가져오기"""
    records_df = read("일일_기록")
    
    # 학생ID와 과목이 일치하는 기록 필터링
    student_records = records_df[(records_df['학생ID'] == student_id) & (records_df['과목'] == subject)]
    
    # 날짜 기준 내림차순 정렬
    if not student_records.empty:
        student_records['날짜'] = pd.to_datetime(student_records['날짜'])
        student_records = student_records.sort_values('날짜', ascending=False)
        
        # 가장 최근 기록 반환
        if not student_records.empty:
            latest_record = student_records.iloc[0]
            return {
                '마지막 수업일': latest_record['날짜'].strftime('%Y-%m-%d'),
                '진도': latest_record['진도'],
                '다음진도계획': latest_record['다음진도계획'],
                '특이사항': latest_record['특이사항']
            }
    
    return {
        '마지막 수업일': '기록 없음',
        '진도': '기록 없음',
        '다음진도계획': '기록 없음',
        '특이사항': '기록 없음'
    }

def save_attendance_record(record_data):
    """출석 및 진도 기록 저장"""
    # 기록ID 생성 (날짜_학생ID_과목)
    record_id = f"{record_data['날짜']}_{record_data['학생ID']}_{record_data['과목']}"
    record_data['기록ID'] = record_id
    
    # 데이터프레임으로 변환하여 쓰기
    record_df = pd.DataFrame([record_data])
    
    # 기존 기록 불러오기
    records_df = read("일일_기록")
    
    # 동일한 기록ID가 있는지 확인
    existing_record = records_df[records_df['기록ID'] == record_id]
    
    if existing_record.empty:
        # 새 기록 추가
        updated_records = pd.concat([records_df, record_df], ignore_index=True)
    else:
        # 기존 기록 업데이트
        records_df = records_df[records_df['기록ID'] != record_id]
        updated_records = pd.concat([records_df, record_df], ignore_index=True)
    
    # 저장
    write(updated_records, "일일_기록")
    return True

# Streamlit 앱 시작
st.title("영어 교육 관리 시스템")

# 세션 상태 초기화
if 'login' not in st.session_state:
    st.session_state.login = None

# 로그인 상태가 아니면 로그인 폼 표시
if not st.session_state.login:
    st.subheader("강사 로그인")
    
    with st.form("login_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        login_button = st.form_submit_button("로그인")
        
        if login_button:
            teacher = get_teacher_by_credentials(email, password)
            if teacher:
                st.session_state.login = teacher
                st.experimental_rerun()
            else:
                st.error("로그인 정보가 올바르지 않습니다.")
else:
    # 로그인 상태일 때 메인 대시보드 표시
    teacher = st.session_state.login
    st.success(f"{teacher['이름']} 강사님 환영합니다!")
    
    if st.button("로그아웃"):
        st.session_state.login = None
        st.experimental_rerun()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["오늘의 수업", "학생 관리", "기록 확인"])
    
    with tab1:
        st.subheader("오늘의 수업")
        
        # 오늘 수업할 학생 및 과목 정보 가져오기
        today_classes = get_today_classes(teacher['강사ID'])
        
        if today_classes.empty:
            st.info("오늘 예정된 수업이 없습니다.")
        else:
            # 학생별로 그룹화
            for student_id, group in today_classes.groupby('학생ID'):
                student_name = group['학생이름'].iloc[0]
                st.markdown(f"### {student_name}")
                
                # 학생이 수강하는 각 과목에 대한 이전 진도 및 출석 기록 폼
                for _, row in group.iterrows():
                    subject = row['과목']
                    
                    # 이전 진도 정보 가져오기
                    previous_progress = get_previous_progress(student_id, subject)
                    
                    # 과목별 정보 표시
                    st.markdown(f"#### 과목: {subject}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**이전 수업 정보**")
                        st.markdown(f"마지막 수업일: {previous_progress['마지막 수업일']}")
                        st.markdown(f"진행한 진도: {previous_progress['진도']}")
                        st.markdown(f"계획된 다음 진도: {previous_progress['다음진도계획']}")
                        if previous_progress['특이사항'] != '기록 없음' and previous_progress['특이사항']:
                            st.markdown(f"특이사항: {previous_progress['특이사항']}")
                    
                    with col2:
                        # 출석 및 진도 기록 폼
                        with st.form(f"attendance_form_{student_id}_{subject}"):
                            st.markdown("**오늘 수업 기록**")
                            
                            attendance = st.selectbox(
                                "출석 상태",
                                options=["출석", "지각", "결석"],
                                key=f"attendance_{student_id}_{subject}"
                            )
                            
                            # 결석인 경우 사유 입력 필드 표시
                            absence_reason = ""
                            if attendance == "결석":
                                absence_reason = st.selectbox(
                                    "결석 사유",
                                    options=["질병", "가족행사", "학교행사", "여행", "기타"],
                                    key=f"reason_{student_id}_{subject}"
                                )
                                if absence_reason == "기타":
                                    absence_reason = st.text_input(
                                        "기타 사유",
                                        key=f"other_reason_{student_id}_{subject}"
                                    )
                            
                            # 진도 및 특이사항 입력
                            progress = st.text_area(
                                "오늘 진행한 진도",
                                key=f"progress_{student_id}_{subject}"
                            )
                            
                            next_progress = st.text_area(
                                "다음 진도 계획",
                                key=f"next_progress_{student_id}_{subject}"
                            )
                            
                            notes = st.text_area(
                                "특이사항",
                                key=f"notes_{student_id}_{subject}"
                            )
                            
                            submit = st.form_submit_button("저장")
                            
                            if submit:
                                # 기록 데이터 생성
                                record_data = {
                                    '날짜': row['날짜'],
                                    '학생ID': student_id,
                                    '강사ID': teacher['강사ID'],
                                    '과목': subject,
                                    '출석상태': attendance,
                                    '결석사유': absence_reason if attendance == "결석" else "",
                                    '진도': progress,
                                    '다음진도계획': next_progress,
                                    '특이사항': notes
                                }
                                
                                # 기록 저장
                                if save_attendance_record(record_data):
                                    st.success(f"{student_name}의 {subject} 수업 기록이 저장되었습니다.")
                                else:
                                    st.error("기록 저장 중 오류가 발생했습니다.")
                    
                    st.markdown("---")
    
    with tab2:
        st.subheader("학생 관리")
        
        # 강사가 담당하는 학생 목록 표시
        students_df = get_students_for_teacher(teacher['강사ID'])
        
        if students_df.empty:
            st.info("담당하는 학생이 없습니다.")
        else:
            # 학생 선택 드롭다운
            selected_student = st.selectbox(
                "학생 선택",
                options=students_df['이름'].tolist(),
                key="student_select"
            )
            
            # 선택된 학생 정보 표시
            student_info = students_df[students_df['이름'] == selected_student].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**기본 정보**")
                st.markdown(f"이름: {student_info['이름']}")
                st.markdown(f"나이: {student_info['나이']}")
                st.markdown(f"학년: {student_info['학년']}")
                st.markdown(f"연락처: {student_info['연락처']}")
                st.markdown(f"학부모 연락처: {student_info['학부모연락처']}")
                st.markdown(f"등록일: {student_info['등록일']}")
            
            with col2:
                st.markdown("**수강 정보**")
                subjects = student_info['수강과목'].split(',')
                for subject in subjects:
                    st.markdown(f"- {subject.strip()}")
            
            # 학생의 과목별 진도 현황 표시
            st.markdown("### 과목별 진도 현황")
            
            for subject in subjects:
                subject = subject.strip()
                st.markdown(f"#### {subject}")
                
                # 과목별 기록 가져오기
                records_df = read("일일_기록")
                subject_records = records_df[
                    (records_df['학생ID'] == student_info['학생ID']) & 
                    (records_df['과목'] == subject)
                ]
                
                if subject_records.empty:
                    st.info(f"{subject} 과목의 기록이 없습니다.")
                else:
                    # 날짜 기준 내림차순 정렬
                    subject_records['날짜'] = pd.to_datetime(subject_records['날짜'])
                    subject_records = subject_records.sort_values('날짜', ascending=False)
                    
                    # 최근 5개 기록만 표시
                    recent_records = subject_records.head(5)
                    
                    for _, record in recent_records.iterrows():
                        st.markdown(f"**{record['날짜'].strftime('%Y-%m-%d')}**")
                        st.markdown(f"출석: {record['출석상태']}")
                        if record['출석상태'] == '결석' and record['결석사유']:
                            st.markdown(f"결석사유: {record['결석사유']}")
                        st.markdown(f"진도: {record['진도']}")
                        st.markdown(f"다음 진도 계획: {record['다음진도계획']}")
                        if record['특이사항']:
                            st.markdown(f"특이사항: {record['특이사항']}")
                        st.markdown("---")
    
    with tab3:
        st.subheader("기록 확인")
        
        # 날짜 선택
        selected_date = st.date_input(
            "날짜 선택",
            value=datetime.now(KST).date()
        )
        
        # 선택된 날짜의 기록 가져오기
        records_df = read("일일_기록")
        
        if not records_df.empty:
            # 날짜 형식 변환
            records_df['날짜'] = pd.to_datetime(records_df['날짜']).dt.date
            date_records = records_df[
                (records_df['날짜'] == selected_date) & 
                (records_df['강사ID'] == teacher['강사ID'])
            ]
            
            if date_records.empty:
                st.info(f"{selected_date} 날짜의 기록이 없습니다.")
            else:
                # 학생 이름 정보 추가
                students_df = read("학생_마스터")
                date_records = date_records.merge(
                    students_df[['학생ID', '이름']],
                    on='학생ID',
                    how='left'
                )
                
                # 학생별로 그룹화하여 표시
                for student_id, group in date_records.groupby('학생ID'):
                    student_name = group['이름'].iloc[0]
                    st.markdown(f"### {student_name}")
                    
                    for _, record in group.iterrows():
                        st.markdown(f"**과목: {record['과목']}**")
                        st.markdown(f"출석: {record['출석상태']}")
                        if record['출석상태'] == '결석' and record['결석사유']:
                            st.markdown(f"결석사유: {record['결석사유']}")
                        st.markdown(f"진도: {record['진도']}")
                        st.markdown(f"다음 진도 계획: {record['다음진도계획']}")
                        if record['특이사항']:
                            st.markdown(f"특이사항: {record['특이사항']}")
                        st.markdown("---")
