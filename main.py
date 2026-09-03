import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 2. 제목 및 설명
st.title("🌡️ 서울 100년 연평균 기온 변화 분석")
st.markdown(
    """
    본 애플리케이션은 **서울의 지난 100여 년간(1907년~) 기온 데이터**를 바탕으로,
    연평균 기온의 장기적인 변화 추이와 모든 속성값의 요약 통계를 제공합니다.
    """
)

# 3. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    try:
        df = pd.read_csv(url, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(url, encoding="utf-8")
    
    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()
    
    # 모든 컬럼 자동 인식 (날짜, 지점, 평균기온, 최저기온, 최고기온)
    date_col = [c for c in df.columns if "날짜" in c][0]
    point_col = [c for c in df.columns if "지점" in c][0]
    avg_temp_col = [c for c in df.columns if "평균" in c][0]
    min_temp_col = [c for c in df.columns if "최저" in c][0]
    max_temp_col = [c for c in df.columns if "최고" in c][0]
    
    # 데이터 타입 변환 및 연도 추출
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["연도"] = df[date_col].dt.year
    
    # 수치형 변환
    df[point_col] = pd.to_numeric(df[point_col], errors="coerce")
    for col in [avg_temp_col, min_temp_col, max_temp_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # 연도별 집계
    yearly_df = df.groupby("연도")[avg_temp_col].agg(["mean", "min", "max"]).reset_index()
    yearly_df.columns = ["연도", "연평균기온", "최저기온_연중최저", "최고기온_연중최고"]
    yearly_df["연평균기온"] = yearly_df["연평균기온"].round(2)
    yearly_df["5년_이동평균"] = yearly_df["연평균기온"].rolling(window=5, min_periods=1).mean().round(2)
    
    cols_dict = {
        "date": date_col,
        "point": point_col,
        "avg": avg_temp_col,
        "min": min_temp_col,
        "max": max_temp_col
    }
    
    return yearly_df, df, cols_dict

# 데이터 로딩
try:
    yearly_df, raw_df, cols = load_data()
    
    # 4. 사이드바 - 조회 구간 설정
    st.sidebar.header("⚙️ 분석 설정")
    min_year = int(yearly_df["연도"].min())
    max_year = int(yearly_df["연도"].max())
    
    selected_years = st.sidebar.slider(
        "조회할 연도 범위를 선택하세요",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    filtered_yearly_df = yearly_df[(yearly_df["연도"] >= selected_years[0]) & (yearly_df["연도"] <= selected_years[1])]
    filtered_raw_df = raw_df[(raw_df["연도"] >= selected_years[0]) & (raw_df["연도"] <= selected_years[1])]
    
    # 5. 핵심 지표 메트릭
    st.subheader("📊 주요 기온 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    avg_temp_all = filtered_yearly_df["연평균기온"].mean()
    start_temp = filtered_yearly_df.iloc[0]["연평균기온"]
    end_temp = filtered_yearly_df.iloc[-1]["연평균기온"]
    temp_diff = round(end_temp - start_temp, 2)
    max_temp_year = filtered_yearly_df.loc[filtered_yearly_df["연평균기온"].idxmax()]
    
    col1.metric("선택 구간 전체 연평균", f"{avg_temp_all:.2f} °C")
    col2.metric(f"시작 연도 ({int(filtered_yearly_df.iloc[0]['연도'])})", f"{start_temp} °C")
    col3.metric(f"최근 연도 ({int(filtered_yearly_df.iloc[-1]['연도'])})", f"{end_temp} °C", delta=f"{temp_diff:+.2f} °C")
    col4.metric(f"역대 최고 연평균 ({int(max_temp_year['연도'])})", f"{max_temp_year['연평균기온']} °C")
    
    st.markdown("---")
    
    # 6. 연평균 기온 변화 차트
    st.subheader("📈 연평균 기온 변화 추이")
    
    fig = px.line(
        filtered_yearly_df,
        x="연도",
        y=["연평균기온", "5년_이동평균"],
        title=f"서울 연평균 기온 변화 ({selected_years[0]}년 ~ {selected_years[1]}년)",
        labels={"value": "기온 (°C)", "연도": "연도", "variable": "구분"},
        markers=True
    )
    
    fig.add_scatter(
        x=filtered_yearly_df["연도"],
        y=filtered_yearly_df["연평균기온"],
        mode="lines",
        line=dict(dash="dash", color="rgba(255, 99, 132, 0.6)"),
        name="선형 추세선"
    )
    
    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(showgrid=True),
        yaxis=dict(title="기온 (°C)", showgrid=True),
        legend=dict(title="구분", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 7. 전체 속성(지점, 평균기온, 최저기온, 최고기온) 요약 통계
    st.subheader("📋 원본 데이터 전체 속성 요약 통계")
    st.caption(f"선택한 구간({selected_years[0]}년 ~ {selected_years[1]}년) 동안 수집된 원본 데이터의 모든 수치 속성 통계량입니다.")
    
    # 원본 CSV의 모든 속성 포함 (지점, 평균기온, 최저기온, 최고기온)
    all_target_cols = [cols["point"], cols["avg"], cols["min"], cols["max"]]
    summary_stats = filtered_raw_df[all_target_cols].describe().T
    
    summary_stats = summary_stats.rename(columns={
        "count": "관측 수(건)",
        "mean": "평균",
        "std": "표준편차",
        "min": "최소값",
        "25%": "25% 백분위",
        "50%": "중앙값(50%)",
        "75%": "75% 백분위",
        "max": "최대값"
    })
    
    st.dataframe(summary_stats.round(2), use_container_width=True)
    
    # 8. 상세 데이터 보기 (탭)
    with st.expander("📄 상세 데이터 테이블 보기"):
        tab1, tab2 = st.tabs(["연도별 집계 데이터", "일별 원본 전체 데이터"])
        with tab1:
            st.dataframe(filtered_yearly_df, use_container_width=True)
        with tab2:
            st.dataframe(filtered_raw_df[[cols["date"], cols["point"], cols["avg"], cols["min"], cols["max"]]], use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
