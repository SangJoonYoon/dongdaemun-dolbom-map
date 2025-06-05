import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import st_folium

# ─── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="동대문구 건강지원센터",
    page_icon="🏥",
    layout="wide",
)

# ─── 1) centers.csv 로드 및 기본 검증 ─────────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다. 앱 루트 디렉터리에 centers.csv를 두세요.")
    st.stop()

required_cols = {"name", "feature", "dong", "programs", "categories", "lat", "lng"}
if not required_cols.issubset(centers.columns):
    missing = required_cols - set(centers.columns)
    st.error(f"❗ centers.csv에 다음 컬럼이 반드시 있어야 합니다: {', '.join(missing)}")
    st.stop()

# ─── 2) 상단 탭 구성 ─────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["소개", "건강지원센터지도", "프로그램 목록", "프로그램 신청"])


# ─── 3) 1️⃣ 소개 페이지 ─────────────────────────────────────
with tab1:
    st.markdown(
        """
        # 🏥 동대문구 건강지원센터

        동대문구내 **14개 행정동**(용신동, 제기동, 전농1·2동, 답십리1·2동, 장안1·2동, 청량리동, 회기동, 휘경1·2동, 이문1·2동)에 
        건강지원센터를 설치하여, 주민들의 **만성질환 예방**, **정신건강 증진**, **건강생활습관 개선** 등을 지원합니다.

        ---
        
        ### 주요 운영 방침
        1. **동별 균형 배치**  
           - 공공데이터(동별 인구 및 의료기관 분포)를 바탕으로 의료 사각지대 해소  
           - 상위 3개 동(휘경2동, 이문2동, 답십리2동) 집중 지원

        2. **병원 연계 사후관리**  
           - 지역 병·의원 연계 후진료 환자 사후관리  
           - 미진료 주민 대상 기초검진·상담 제공  

        3. **맞춤형 건강증진 프로그램**  
           - 연령·타깃별 프로그램 구성 (노인, 청소년, 임산부, 성인)  
           - 운동, 영양, 정신건강, 금연·금주 등 다양한 테마

        4. **건강동아리 구성**  
           - 보건소·학교·복지관 등과 협력  
           - 독거노인·청소년·임산부 중심 소모임 활동 지원

        ### 🎯 목표
        1. **만성질환 조기 예방** (고혈압·당뇨·심뇌혈관질환 등)  
        2. **정신건강 지원** (우울·스트레스 관리 등)  
        3. **건강생활문화 확산** (영양, 운동, 금연 프로그램)  
        4. **의료 사각지대 해소 및 지역 공동체 강화**

        > *“건강은 삶의 기본입니다. 동대문구 건강지원센터와 함께 더 건강한 내일을 만들어갑니다.”*

        """
    )


# ─── 4) 2️⃣ 건강지원센터지도 페이지 ─────────────────────────────────
with tab2:
    st.header("📍 건강지원센터 위치 지도")
    st.write("우측에서 ‘전체’ 혹은 특정 행정동을 선택하시면 해당 동의 건강지원센터 위치가 표시됩니다.")

    # 4-1) 동 선택용 Selectbox (전체 + 14개 행정동 중 3개만 실제 마커 있음)
    all_dongs = ["전체"] + sorted(centers["dong"].unique())
    sel_dong = st.selectbox("▸ 행정동 선택", options=all_dongs, index=0)

    # 4-2) 필터링된 데이터프레임 생성
    if sel_dong == "전체":
        # “전체”일 때는 14개 중 실제 데이터가 존재하는 모든 센터를 띄움
        df = centers.copy()
    else:
        df = centers[centers["dong"] == sel_dong].copy()

    st.caption(f"표시된 센터: {len(df)}개")

    # 4-3) 지도 중심 좌표 및 줌 결정
    if len(df) > 0:
        if sel_dong == "전체":
            lat_center = df["lat"].mean()
            lng_center = df["lng"].mean()
            zoom_level = 12
        else:
            lat_center = float(df.iloc[0]["lat"])
            lng_center = float(df.iloc[0]["lng"])
            zoom_level = 15
    else:
        # 데이터가 없을 경우(해당 동에 센터 데이터가 없으면 기본값)
        lat_center, lng_center, zoom_level = 37.574360, 127.039530, 13

    # 4-4) Folium 지도 생성
    m = folium.Map(location=[lat_center, lng_center], zoom_start=zoom_level, tiles="cartodbpositron")

    # 4-5) GeoJSON으로 행정동 경계 하이라이트
    GEO_URL = (
        "https://raw.githubusercontent.com/"
        "raqoon886/Local_HangJeongDong/master/"
        "hangjeongdong_서울특별시.geojson"
    )
    try:
        res = requests.get(GEO_URL, timeout=10)
        res.raise_for_status()
        gj = res.json()

        def style_fn(feature):
            # feature['properties']['adm_nm'] 에 행정동 이름이 들어있음
            name = feature["properties"].get("adm_nm", "")
            # “전체”가 아니고, 선택된 동 이름이 포함되면 파란색으로 하이라이트
            is_selected = (sel_dong != "전체" and sel_dong in name)
            return {
                "fillColor": "#0055FF" if is_selected else "#ffffff",
                "color":     "#0055FF" if is_selected else "#999999",
                "weight":    2 if is_selected else 1,
                "fillOpacity": 0.3 if is_selected else 0.0
            }

        folium.GeoJson(
            gj,
            style_function=style_fn,
            tooltip=folium.GeoJsonTooltip(fields=["adm_nm"], aliases=["행정동"])
        ).add_to(m)
    except Exception as e:
        st.warning("⚠️ 행정동 경계 데이터 로드에 실패했습니다.")

    # 4-6) 센터 마커 추가 (클러스터 없음)
    for _, row in df.drop_duplicates(subset=["name"]).iterrows():
        title = row["name"].replace("돌봄센터", "건강지원센터")
        # 프로그램 목록 HTML (<li> 태그)
        prog_items = "".join(f"<li>{p.strip()}</li>" for p in row["programs"].split(";"))
        # 카테고리 태그 HTML (<span> 태그)
        cat_items = "".join(
            f"<span style='display:inline-block; background:#E3F2FD; color:#0D47A1; "
            f"padding:3px 8px; margin:2px; border-radius:4px; font-size:12px;'>"
            f"#{c.strip()}"
            f"</span>"
            for c in row["categories"].split(";")
        )

        popup_html = f"""
            <div style="max-width:260px; font-family:Arial, sans-serif;">
              <h4 style="margin:0 0 6px;">{title}</h4>
              <p style="margin:0; font-weight:600;">프로그램:</p>
              <ul style="margin:4px 0 0 12px 16px; padding:0; list-style:disc;">
                {prog_items}
              </ul>
              <p style="margin:6px 0 0 0; font-weight:600;">태그:</p>
              <div style="margin-top:4px;">{cat_items}</div>
            </div>
        """
        folium.Marker(
            location=[row["lat"], row["lng"]],
            tooltip=title,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="green", icon="plus-sign")
        ).add_to(m)

    # 4-7) Folium 지도를 Streamlit 화면에 렌더링
    st_folium(m, width="100%", height=650)


# ─── 5) 3️⃣ 프로그램 목록 페이지 ─────────────────────────────────
with tab3:
    st.title("📋 운영 중인 프로그램 목록")
    st.write("각 프로그램을 클릭하면 제공하는 센터 목록을 확인할 수 있습니다.")

    # “programs” 컬럼을 세미콜론으로 분리 → explode → 빈 문자열 제거
    dfp = centers[["name", "programs", "categories", "dong"]].copy().fillna("")
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    dfp = dfp[dfp["programs"] != ""]

    # 프로그램별로 그룹핑 → Expander 형태로 출력
    for prog_name, grp in dfp.groupby("programs"):
        # 해당 프로그램에 속한 센터 이름 리스트
        center_names = grp["name"].tolist()
        # 카테고리 태그(노인·성인·임산부·청소년·일반) 모아서 태그 표시
        cat_set = set()
        _ = grp["categories"].str.split(";").apply(lambda arr: cat_set.update([x.strip() for x in arr if x.strip()]))
        cat_tags = " ".join(f"`#{c}`" for c in sorted(cat_set))
        with st.expander(f"{prog_name} ({len(center_names)}개 센터) {cat_tags}"):
            for _, row2 in grp.iterrows():
                st.write(f"- {row2['name']} ({row2['dong']})")


# ─── 6) 4️⃣ 프로그램 신청 페이지 ─────────────────────────────────
with tab4:
    st.title("📝 프로그램 신청")
    st.write("원하시는 프로그램을 선택하고, 정보를 입력한 뒤 ‘신청하기’ 버튼을 클릭해 주세요.")

    dfp = centers[["programs"]].copy().fillna("")
    dfp["programs"] = dfp["programs"].str.split(";")
    dfp = dfp.explode("programs")
    dfp["programs"] = dfp["programs"].str.strip()
    programs = sorted(dfp[dfp["programs"] != ""].programs.unique())

    if not programs:
        st.info("현재 등록된 프로그램이 없습니다.")
        st.stop()

    sel_prog = st.selectbox("▸ 프로그램 선택", programs)
    user_name = st.text_input("▸ 이름")
    contact = st.text_input("▸ 연락처 (예: 010-1234-5678)")

    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 올바르게 입력해 주세요.")
