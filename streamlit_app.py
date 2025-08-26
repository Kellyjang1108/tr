# 스프레드시트 연결 테스트
if st.button("스프레드시트 연결 테스트"):
    client = connect()
    if client:
        try:
            spreadsheet_id = st.secrets["general"]["spreadsheet_id"]
            st.write(f"연결 시도 중인 스프레드시트 ID: {spreadsheet_id}")
            
            # 다양한 방법으로 시도
            try:
                sheet = client.open_by_key(spreadsheet_id)
                st.success(f"Key로 연결 성공: '{sheet.title}'")
            except Exception as e1:
                st.error(f"Key로 연결 실패: {str(e1)}")
                
                # URL로 시도
                try:
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                    sheet = client.open_by_url(sheet_url)
                    st.success(f"URL로 연결 성공: '{sheet.title}'")
                except Exception as e2:
                    st.error(f"URL로 연결 실패: {str(e2)}")
                    
                    # 이름으로 시도 (스프레드시트 이름을 알고 있다면)
                    try:
                        sheet = client.open("학생진도관리")  # 스프레드시트 이름으로 변경
                        st.success(f"이름으로 연결 성공: '{sheet.title}'")
                    except Exception as e3:
                        st.error(f"이름으로 연결 실패: {str(e3)}")
            
            # 스프레드시트 목록 가져오기
            try:
                all_sheets = client.list_spreadsheet_files()
                st.write("사용 가능한 스프레드시트 목록:")
                for s in all_sheets:
                    st.write(f"- {s['name']} (ID: {s['id']})")
            except Exception as e4:
                st.error(f"스프레드시트 목록 가져오기 실패: {str(e4)}")
                
        except Exception as e:
            st.error(f"스프레드시트 연결 오류: {e}")
            st.write("오류 세부 정보:", str(e))
