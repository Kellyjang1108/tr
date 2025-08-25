# 로그인 부분만 수정
if st.button("로그인"):
    df = read("강사_마스터")
    st.write("데이터:", df)  # 디버깅용
    
    if not df.empty:
        # 컬럼명 무시하고 위치로 접근
        for i, row in df.iterrows():
            if str(row.iloc[0]) == id and str(row.iloc[2]) == pw:
                st.session_state.login = True
                st.session_state.name = row.iloc[1]
                st.rerun()
    st.error("실패")
