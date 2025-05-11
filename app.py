# ─── 3️⃣ 프로그램 목록 페이지 ─────────────────────────────────
elif page == "프로그램 목록":
    st.title("📋 프로그램 목록")
    # programs 칼럼을 문자열로 변환 후 분리 → explode → 빈값 제거 → 고유화
    progs = (
        centers["programs"]
        .fillna("")                # NaN → ""
        .astype(str)               # 모두 문자열로
        .str.split(";")            # ";" 로 분리
        .explode()                 # 행별로 펼치기
        .str.strip()               # 앞뒤 공백 제거
    )
    progs = progs[progs != ""]     # 빈 문자열 제거
    progs = sorted(progs.unique())  # 중복 제거 후 정렬

    if not progs:
        st.info("등록된 프로그램이 없습니다.")
    else:
        for p in progs:
            st.markdown(f"- {p}")

# ─── 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
else:  # 프로그램 신청
    st.title("📝 프로그램 신청")
    # 위와 동일한 방식으로 프로그램 리스트 생성
    programs = (
        centers["programs"]
        .fillna("")
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
    )
    programs = sorted(programs[programs != ""].unique())

    if not programs:
        st.info("등록된 프로그램이 없습니다.")
        st.stop()

    sel_prog     = st.selectbox("프로그램 선택", programs)
    user_name    = st.text_input("이름")
    contact      = st.text_input("연락처", placeholder="010-1234-5678")

    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
