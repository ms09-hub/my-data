import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 2. 앱 제목 및 데이터 소스 안내
st.title("🌡️ 서울 100년 연평균 기온 변화 분석")
st.markdown("지난 100여 년간 서울의 연평균 기온 변화 추이 및 5년 이동평균선 시각화 앱입니다.")

# 3. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리 (CP949 / UTF-8)
    try:
        df = pd.read_csv(url, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(url, encoding="utf-8")
    
    # 공백 제거 및 열 이름 자동 탐색
    df.columns = df.columns.str.strip()
    date_col = [c for c in df.columns if "날짜" in c][0]
    avg_temp_col = [c for c in df.columns if "평균" in c][0]
    
    # 타입 변환 및 연도 추출
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["연도"] = df[date_col].dt.year
    df[avg_temp_col] = pd.to_numeric(df[avg_temp_col], errors="coerce")
    
    # 연도별 평균 기온 계산 및 이동평균 산출
    yearly_df = df.groupby("연도")[avg_temp_col].agg(["mean", "min", "max"]).reset_index()
    yearly_df.columns = ["연도", "연평균기온", "최저기온_연중최저", "최고기온_연중최고"]
    yearly_df["연평균기온"] = yearly_df["연평균기온"].round(2)
    yearly_df["5년_이동평균"] = yearly_df["연평균기온"].rolling(window=5, min_periods=1).mean().round(2)
    
    return yearly_df

try:
    yearly_df = load_data()
    
    # 4. 사이드바 - 조절 슬라이더
    st.sidebar.header("⚙️ 필터 설정")
    min_year = int(yearly_df["연도"].min())
    max_year = int(yearly_df["연도"].max())
    
    selected_years = st.sidebar.slider(
        "조회할 연도 범위를 선택하세요",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    filtered_df = yearly_df[(yearly_df["연도"] >= selected_years[0]) & (yearly_df["연도"] <= selected_years[1])]
    
    # 5. 요약 지표 (Metrics)
    st.subheader("📊 주요 기온 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    avg_temp_all = filtered_df["연평균기온"].mean()
    start_temp = filtered_df.iloc[0]["연평균기온"]
    end_temp = filtered_df.iloc[-1]["연평균기온"]
    temp_diff = round(end_temp - start_temp, 2)
    max_temp_row = filtered_df.loc[filtered_df["연평균기온"].idxmax()]
    
    col1.metric("선택 구간 연평균", f"{avg_temp_all:.2f} °C")
    col2.metric(f"시작 연도 ({int(filtered_df.iloc[0]['연도'])})", f"{start_temp} °C")
    col3.metric(f"최근 연도 ({int(filtered_df.iloc[-1]['연도'])})", f"{end_temp} °C", delta=f"{temp_diff:+.2f} °C")
    col4.metric(f"최고 연평균 ({int(max_temp_row['연도'])})", f"{max_temp_row['연평균기온']} °C")
    
    st.markdown("---")
    
    # 6. Plotly 인터랙티브 그래프
    st.subheader("📈 연평균 기온 변화 추이")
    fig = px.line(
        filtered_df,
        x="연도",
        y=["연평균기온", "5년_이동평균"],
        labels={"value": "기온 (°C)", "연도": "연도", "variable": "구분"},
        markers=True
    )
    
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 7. 상세 데이터 표
    with st.expander("📄 상세 데이터 보기"):
        st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
