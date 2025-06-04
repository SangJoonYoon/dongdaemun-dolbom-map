import os
import json
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ─── 페이지 설정 ─────────────────────────────────────────
st.set_page_config(page_title="동대문구 건강지원센터", layout="wide")

# ─── Kakao JS Key 로드 ────────────────────────────────────
# Streamlit Cloud 사용 시: Manage app → Settings → Secrets 에서
# KAKAO_JS_KEY="여기에_JavaScript_키" 형태로 저장해주세요.
KAKAO_JS_KEY = os.environ.get("KAKAO_JS_KEY")
if not KAKAO_JS_KEY:
    st.error("❗ Kakao JavaScript 키를 Settings → Secrets → KAKAO_JS_KEY에 설정해주세요.")
    st.stop()

# ─── CSS (배지 스타일) ────────────────────────────────────
st.markdown("""
<style>
.badge {
  display:inline-block;
  background:#3498db;
  color:white;
  padding:2px 6px;
  margin:0 2px;
  border-radius:4px;
  font-size:0.85em;
}
</style>
""", unsafe_allow_html=True)

# ─── 데이터 로드 & 검증 ───────────────────────────────────
try:
    centers = pd.read_csv("centers.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("❗ centers.csv 파일을 찾을 수 없습니다.")
    st.stop()

required = {"name","feature","dong","programs","categories","lat","lng"}
if not required.issubset(centers.columns):
    st.error(f"❗ centers.csv에 다음 컬럼이 필요합니다: {', '.join(sorted(required))}")
    st.stop()

# ─── 탭 메뉴 ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["소개","건강지원센터지도","프로그램 목록","프로그램 신청"])

# ─── 1️⃣ 소개 ─────────────────────────────────────────────
with tab1:
    st.header("🏥 동대문구 건강지원센터 소개")
    st.write("동대문구 내 건강지원센터 위치와 프로그램 정보를 한눈에 확인하고, "
             "원하는 프로그램에 바로 신청할 수 있습니다.")

# ─── 2️⃣ 건강지원센터지도 ─────────────────────────────────
with tab2:
    st.header("📍 건강지원센터 위치 지도")
    st.write("아래 버튼을 눌러 원하는 동을 선택하면 해당 동이 확대되고 경계가 하이라이트됩니다.")

    # session_state 초기화
    if "sel_dong" not in st.session_state:
        st.session_state.sel_dong = "전체"

    # 동 선택 버튼
    c_all, c_wi, c_im, c_da = st.columns(4)
    if c_all.button("전체"):
        st.session_state.sel_dong = "전체"
    if c_wi.button("휘경2동"):
        st.session_state.sel_dong = "휘경2동"
    if c_im.button("이문2동"):
        st.session_state.sel_dong = "이문2동"
    if c_da.button("답십리2동"):
        st.session_state.sel_dong = "답십리2동"

    # 센터 데이터를 JSON 으로 변환 (Kakao JS에서 사용)
    centers_js = centers.to_dict(orient="records")
    centers_json = json.dumps(centers_js, ensure_ascii=False)

    # 지도 중심 및 줌 레벨 결정
    if st.session_state.sel_dong == "전체":
        center_lat, center_lng, zoom = 37.582000, 127.064000, 13
    else:
        df_d = centers[centers["dong"] == st.session_state.sel_dong]
        center_lat = float(df_d["lat"].mean())
        center_lng = float(df_d["lng"].mean())
        zoom = 16

    # Kakao Map HTML + JavaScript
    html = f"""
    <div id="map" style="width:100%;height:600px;"></div>
    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
    <script>
      kakao.maps.load(function() {{
        // 1) 지도 생성
        var container = document.getElementById('map');
        var options = {{
          center: new kakao.maps.LatLng({center_lat}, {center_lng}),
          level: {zoom}
        }};
        var map = new kakao.maps.Map(container, options);

        // 2) GeoJSON으로 행정동 경계 불러와서 하이라이트
        fetch("https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_서울특별시.geojson")
          .then(response => response.json())
          .then(data => {{
            data.features.forEach(function(feature) {{
              // 좌표 배열 변환 (예시: 첫 번째 좌표 배열 사용)
              var coords = feature.geometry.coordinates[0].map(function(coord) {{
                return new kakao.maps.LatLng(coord[1], coord[0]);
              }});
              var polygon = new kakao.maps.Polygon({{
                map: map,
                paths: coords,
                strokeWeight: 1,
                strokeColor: "#999999",
                fillColor: "#ffffff",
                fillOpacity: 0.0
              }});
              var admName = feature.properties.adm_nm;
              if ("{st.session_state.sel_dong}" !== "전체" && admName.includes("{st.session_state.sel_dong}")) {{
                polygon.setOptions({{
                  strokeWeight: 3,
                  strokeColor: "#0055FF",
                  fillColor: "#0055FF",
                  fillOpacity: 0.3
                }});
              }}
            }});
          }});

        // 3) 센터 마커 추가 및 팝업
        var centers = {centers_json};
        centers.forEach(function(c) {{
          if ("{st.session_state.sel_dong}" === "전체" || c.dong === "{st.session_state.sel_dong}") {{
            var markerPosition = new kakao.maps.LatLng(c.lat, c.lng);
            var marker = new kakao.maps.Marker({{
              map: map,
              position: markerPosition,
              title: c.name
            }});

            // 프로그램 태그 생성 함수 (JS)
            function makeTags(prog, cat) {{
              var tags = [];
              tags.push("#" + cat);
              if (prog.match(/예방|검진|금연/)) tags.push("#예방");
              if (prog.match(/정신|우울|스트레스/)) tags.push("#정신건강");
              if (prog.match(/운동|요가|체조|재활/)) tags.push("#운동");
              if (prog.match(/영양/)) tags.push("#영양");
              if (prog.match(/상담/)) tags.push("#상담");
              if (prog.match(/치매/)) tags.push("#치매");
              return tags.map(function(t) {{
                return '<span style="display:inline-block;background:#3498db;color:#fff;padding:2px 6px;margin:0 2px;border-radius:4px;font-size:0.85em;">' + t + '</span>';
              }}).join("");
            }}

            // 팝업 HTML 생성
            var progList = c.programs.split(";");
            var content = '<div style="padding:8px; max-width:300px;"><strong>' + c.name + '</strong><ul style="margin:4px 0 0 12px 16px;padding:0;">';
            progList.forEach(function(p) {{
              var tagHTML = makeTags(p.trim(), c.categories);
              content += '<li style="margin-bottom:4px;"><span style="font-weight:600;">' + p.trim() + '</span> ' + tagHTML + '</li>';
            }});
            content += '</ul></div>';

            var infowindow = new kakao.maps.InfoWindow({{ content: content }});
            kakao.maps.event.addListener(marker, 'click', function() {{
              infowindow.open(map, marker);
            }});
          }}
        }});
      }});
    </script>
    """

    # Streamlit에 HTML 삽입
    components.html(html, height=650, scrolling=False)

# ─── 3️⃣ 프로그램 목록 ───────────────────────────────────
with tab3:
    st.header("📋 프로그램 목록")
    dfp = centers[["name","programs","categories"]].dropna()
    for prog, grp in dfp.groupby("programs"):
        cat = grp["categories"].iloc[0]
        # 태그 생성
        tags = [f"#{cat}"]
        if any(w in prog for w in ["예방","검진","금연"]): tags.append("#예방")
        if any(w in prog for w in ["정신","우울","스트레스"]): tags.append("#정신건강")
        if any(w in prog for w in ["운동","요가","체조","재활"]): tags.append("#운동")
        if "영양" in prog: tags.append("#영양")
        if "상담" in prog: tags.append("#상담")
        if "치매" in prog: tags.append("#치매")
        badges = "".join(f'<span class="badge">{t}</span>' for t in sorted(set(tags)))

        centers_list = ", ".join(grp["name"].unique())
        st.markdown(f"**{prog}** {badges}<br>"
                    f"<span style='color:gray;'>제공 센터: {centers_list}</span>",
                    unsafe_allow_html=True)

# ─── 4️⃣ 프로그램 신청 ─────────────────────────────────
with tab4:
    st.header("📝 프로그램 신청")
    programs = sorted(centers["programs"].unique())
    sel_prog  = st.selectbox("프로그램 선택", programs)
    user_name = st.text_input("이름")
    contact   = st.text_input("연락처", placeholder="010-1234-5678")
    if st.button("신청하기"):
        if sel_prog and user_name and contact:
            st.success(f"✅ '{sel_prog}' 신청이 완료되었습니다!")
        else:
            st.error("❗ 모든 항목을 입력해주세요.")
