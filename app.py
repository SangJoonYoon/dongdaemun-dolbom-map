import streamlit as st
import pandas as pd
import folium

# Set page config for wide layout and title
st.set_page_config(page_title="동대문구 돌봄 지도", layout="wide")

# Inject CSS for styling (fonts, spacing, color palette, badges)
st.markdown("""
<style>
    body {
        font-family: 'Helvetica Neue', sans-serif;
        background-color: #f9f9f9;
        color: #333333;
    }
    .stApp { padding: 1rem; }
    h1, h2, h3, h4 {
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .badge {
        display: inline-block;
        padding: 0.3em 0.6em;
        margin: 0 0.2em;
        font-size: 0.85em;
        font-weight: 600;
        color: #fff;
        background-color: #3498db;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Load center/program data
df = pd.read_csv("centers.csv")

# Prepare dong-level tags (based on 고령자 인구 비율 & 의료기관 밀도 산식):contentReference[oaicite:0]{index=0}
dong_tags = {
    "휘경2동": ["#고령인구많음", "#의료기관부족"],
    "이문2동": ["#의료기관부족"],
    "답십리2동": ["#고령인구많음", "#의료기관부족"]
}

# Create tabs for sections
tabs = st.tabs(["소개", "건강지원센터 지도", "프로그램 목록", "프로그램 신청"])

# 1. Introduction tab
with tabs[0]:
    st.header("소개")
    st.write("동대문구 건강돌봄 지도 웹앱에 오신 것을 환영합니다. 이 앱은 동대문구 내 건강지원센터 현황과 프로그램 정보를 제공합니다.")
    st.write("지도를 통해 지역별 건강지원센터의 위치와 특성을 확인하고, 다양한 건강 지원 프로그램을 찾아볼 수 있습니다. "
             "대상자별 맞춤 프로그램과 건강 증진을 위한 정보를 손쉽게 얻어보세요.")

# 2. Map tab
with tabs[1]:
    st.header("건강지원센터 지도")
    # Use unique centers for mapping to avoid duplicate markers
    centers = df[['Dong', 'CenterName', 'Latitude', 'Longitude']].drop_duplicates()
    # Initialize folium map centered roughly at Dongdaemun
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=13)
    # Add a marker for each center with popup showing center name and dong tags
    for _, row in centers.iterrows():
        dong = row['Dong']; name = row['CenterName']
        lat = row['Latitude']; lon = row['Longitude']
        tags_html = " ".join([
            f"<span style=\"background-color:#3498db; padding:2px 5px; border-radius:5px; color:white; font-size:0.85em;\">{tag}</span>"
            for tag in dong_tags.get(dong, [])
        ])
        popup_html = f"<b>{name}</b><br/>{tags_html}"
        folium.Marker([lat, lon], popup=popup_html).add_to(m)
    # Display map in Streamlit
    st.components.v1.html(m._repr_html_(), width=800, height=600)

# 3. Program list tab
with tabs[2]:
    st.header("프로그램 목록")
    # Optional filter by target category
    categories = sorted([c for c in df['Category'].unique() if c != "일반"])
    selected_cats = st.multiselect("대상자별 프로그램 필터", categories, default=[])
    # Group programs and display each with tags and centers
    for program_name, group in df.groupby('ProgramName'):
        category = group['Category'].iloc[0]
        if selected_cats and category not in selected_cats:
            continue  # skip if not matching filter
        # Infer tags from program name (target group + purpose)
        target_tag = f"#{category}" if category in ["노인", "청소년", "아동", "임산부", "장애인", "여성", "남성"] else ""
        purpose_tags = []
        if any(word in program_name for word in ["정신", "우울", "스트레스", "심리", "정서"]):
            purpose_tags.append("#정신건강")
        if "예방" in program_name or "금연" in program_name:
            purpose_tags.append("#예방")
        if any(word in program_name for word in ["운동", "체조", "요가", "재활"]):
            purpose_tags.append("#운동")
        if "영양" in program_name:
            purpose_tags.append("#영양")
        if "상담" in program_name:
            purpose_tags.append("#상담")
        if "교육" in program_name:
            purpose_tags.append("#교육")
        if "치매" in program_name:
            purpose_tags.append("#치매")
        if "검진" in program_name:
            purpose_tags.append("#검진")
        purpose_tags = sorted(set(purpose_tags))
        all_tags = ([target_tag] if target_tag else []) + purpose_tags
        tags_html = " ".join(f"<span class='badge'>{tag}</span>" for tag in all_tags)
        centers_list = sorted(group['CenterName'].unique())
        centers_str = ", ".join(centers_list)
        st.markdown(f"**{program_name}** {tags_html}<br/>"
                    f"<span style='color:gray; font-size:0.9em;'>**제공 센터:** {centers_str}</span>",
                    unsafe_allow_html=True)

# 4. Program application tab
with tabs[3]:
    st.header("프로그램 신청")
    st.write("참여를 원하는 프로그램을 선택하고 신청자 정보를 입력해주세요.")
    with st.form(key="apply_form"):
        program_options = sorted(df['ProgramName'].unique())
        chosen_program = st.selectbox("프로그램 선택", program_options)
        name = st.text_input("이름")
        contact = st.text_input("연락처")
        agree = st.checkbox("개인정보 제공에 동의합니다")
        submitted = st.form_submit_button("신청")
        if submitted:
            if not (name and contact and agree):
                st.error("모든 정보를 입력하고 동의에 체크해주세요.")
            else:
                st.success(f"✔️ {name} 님, '{chosen_program}' 프로그램 신청이 완료되었습니다!")
                st.balloons()
