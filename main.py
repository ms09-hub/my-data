import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    연평균 기온의 장기적인 변화 추이와 결측치(데이터 부재 연도) 및 이상치(유난히 낮은 연도)를 한눈에 파악할 수 있도록 시각화한 도구입니다.
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
    
    # 연도별 집계 (관측 일수도 함께 계산하여 결측 연도 확인)
    yearly_df = df.groupby("연도").agg(
        연평균기온=(avg_temp_col, "mean"),
        관측일수=(avg_temp_col, "count")
    ).reset_index()
    
    # 전체 연도 범위 재구성 (중간에 빠진 연도를 연속된 시계열로 표시하기 위함)
    full_years = pd.DataFrame({"연도": range(yearly_df["연도"].min(), yearly_df["연도"].max() + 1)})
    yearly_df = pd.merge(full_years, yearly_df, on="연도", how="left")
    
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
    
    # 4. 사이드바 - 조회 구간 및 이상치 기준 설정
    st.sidebar.header("⚙️ 분석 및 탐지 설정")
    min_year = int(yearly_df["연도"].min())
    max_year = int(yearly_df["연도"].max())
    
    selected_years = st.sidebar.slider(
        "조회할 연도 범위를 선택하세요",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    # 이상치(유난히 낮은 기온) 기준 설정 (기본값: 10.0°C 이하)
    low_temp_threshold = st.sidebar.number_input(
        "❄️ '유난히 낮은 연도' 기준 기온 (°C 이하)",
        min_value=0.0,
        max_value=15.0,
        value=10.0,
        step=0.5
    )
    
    filtered_yearly_df = yearly_df[(yearly_df["연도"] >= selected_years[0]) & (yearly_df["연도"] <= selected_years[1])].copy()
    filtered_raw_df = raw_df[(raw_df["연도"] >= selected_years[0]) & (raw_df["연도"] <= selected_years[1])].copy()
    
    # 5. 특이사항(비어있는 연도 / 유난히 낮은 연도) 감지
    missing_years_df = filtered_yearly_df[filtered_yearly_df["연평균기온"].isna()]
    low_temp_df = filtered_yearly_df[filtered_yearly_df["연평균기온"] <= low_temp_threshold]
    
    # 6. 핵심 지표 메트릭
    st.subheader("📊 주요 기온 지표 및 특이 연도 탐지")
    col1, col2, col3, col4 = st.columns(4)
    
    valid_df = filtered_yearly_df.dropna(subset=["연평균기온"])
    avg_temp_all = valid_df["연평균기온"].mean()
    start_temp = valid_df.iloc[0]["연평균기온"]
    end_temp = valid_df.iloc[-1]["연평균기온"]
    temp_diff = round(end_temp - start_temp, 2)
    
    col1.metric("선택 구간 전체 연평균", f"{avg_temp_all:.2f} °C")
    col2.metric(f"시작 연도 ({int(valid_df.iloc[0]['연도'])})", f"{start_temp} °C")
    col3.metric(f"최근 연도 ({int(valid_df.iloc[-1]['연도'])})", f"{end_temp} °C", delta=f"{temp_diff:+.2f} °C")
    col4.metric("⚠️ 특이 탐지 연도 수", f"비어있음 {len(missing_years_df)}개 / 저온 {len(low_temp_df)}개")
    
    # 특이 연도 안내 메시지
    if len(missing_years_df) > 0:
        missing_str = ", ".join(missing_years_df["연도"].astype(str).tolist())
        st.warning(f"🚨 **데이터가 비어 있는(결측) 연도**: {missing_str} (한국전쟁 등 기상관측 중단 기간)")
    if len(low_temp_df) > 0:
        low_str = ", ".join([f"{int(r['연도'])}({r['연평균기온']}°C)" for _, r in low_temp_df.iterrows()])
        st.info(f"❄️ **유난히 낮은 연도 ({low_temp_threshold}°C 이하)**: {low_str}")

    st.markdown("---")
    
    # 7. 연평균 기온 변화 차트 (특이 연도 강조)
    st.subheader("📈 서울 연평균 기온 변화 추이 (이상 연도 강조)")
    
    fig = go.Figure()
    
    # (1) 기본 연평균 기온 선 그래프
    fig.add_trace(
        go.Scatter(
            x=filtered_yearly_df["연도"],
            y=filtered_yearly_df["연평균기온"],
            mode="lines+markers",
            name="연평균기온",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6)
        )
    )
    
    # (2) 5년 이동평균선
    fig.add_trace(
        go.Scatter(
            x=filtered_yearly_df["연도"],
            y=filtered_yearly_df["5년_이동평균"],
            mode="lines",
            name="5년 이동평균",
            line=dict(color="#ff7f0e", width=2.5, dash="dot")
        )
    )
    
    # (3) 유난히 낮은 연도 빨간색 X 큰 마커 및 기온 텍스트 강조
    if len(low_temp_df) > 0:
        fig.add_trace(
            go.Scatter(
                x=low_temp_df["연도"],
                y=low_temp_df["연평균기온"],
                mode="markers+text",
                name=f"유난히 낮은 연도 (≤{low_temp_threshold}°C)",
                marker=dict(color="red", size=14, symbol="x"),
                text=[f"{y}년<br>{t}°C" for y, t in zip(low_temp_df["연도"], low_temp_df["연평균기온"])],
                textposition="bottom center",
                textfont=dict(color="red", size=11)
            )
        )
    
    # (4) 값이 비어있는 연도(결측) 회색 영역 및 세로 주석 강조
    for m_year in missing_years_df["연도"]:
        fig.add_vrect(
            x0=m_year - 0.5,
            x1=m_year + 0.5,
            fillcolor="gray",
            opacity=0.3,
            line_width=1,
            line_color="darkred",
            annotation_text=f"{m_year}년<br>(관측 없음)",
            annotation_position="top left",
            annotation_font=dict(size=10, color="darkred")
        )
    
    fig.update_layout(
        title=f"서울 연평균 기온 및 이상 연도 탐지 ({selected_years[0]}년 ~ {selected_years[1]}년)",
        xaxis=dict(title="연도", showgrid=True),
        yaxis=dict(title="기온 (°C)", showgrid=True),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 8. 요약 통계 (행: 통계 항목, 열: 지점·평균기온·최저기온·최고기온)
    st.subheader("📋 원본 데이터 전체 속성 요약 통계")
    st.caption(f"선택한 구간({selected_years[0]}년 ~ {selected_years[1]}년) 동안 수집된 원본 데이터의 요약 통계표입니다.")
    
    all_target_cols = [cols["point"], cols["avg"], cols["min"], cols["max"]]
    summary_stats = filtered_raw_df[all_target_cols].describe()
    
    summary_stats = summary_stats.rename(index={
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
    
    # 9. 상세 데이터 보기 (탭)
    with st.expander("📄 상세 데이터 테이블 보기"):
        tab1, tab2 = st.tabs(["연도별 집계 데이터", "일별 원본 전체 데이터"])
        with tab1:
            st.dataframe(filtered_yearly_df, use_container_width=True)
        with tab2:
            st.dataframe(filtered_raw_df[[cols["date"], cols["point"], cols["avg"], cols["min"], cols["max"]]], use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
