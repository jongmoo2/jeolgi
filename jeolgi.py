import streamlit as st
from datetime import datetime, timedelta
import pytz
from skyfield.api import load
from skyfield import almanac

# 1. 천체 데이터 캐싱 (최초 1회만 로드하여 속도 최적화)
@st.cache_resource
def load_astronomy_data():
    ts = load.timescale()
    eph = load('de440.bsp')
    return ts, eph

ts, eph = load_astronomy_data()

# --- UI 구성 ---
st.set_page_config(page_title="이분이지(二分二至) 구간 판별기", layout="centered")

st.title("🌓 이분이지(二分二至) 구간 판별 프로그램")
st.write("지정한 날짜와 시각의 직전 절기를 계산하여 현재 어느 구간에 속해 있는지 판별합니다.")

st.sidebar.header("📅 년월일시 입력")

# 사이드바 입력 컴포넌트
input_date = st.sidebar.date_input("날짜 선택", datetime.now().date())
input_hour = st.sidebar.slider("시간 (시)", 0, 23, 12, step=1)
input_minute = st.sidebar.slider("분 (분)", 0, 59, 0, step=1)

if st.sidebar.button("구간 판별하기", type="primary"):
    with st.spinner("Skyfield로 정밀 천체 데이터 계산 중..."):
        try:
            # datetime 객체 생성 및 한국 표준시(KST) 설정
            kst = pytz.timezone('Asia/Seoul')
            local_dt = kst.localize(datetime(
                input_date.year, input_date.month, input_date.day, input_hour, input_minute
            ))
            
            # 검색 범위 설정 (입력일 기준 185일 전부터 입력일까지)
            t0 = ts.from_datetime(kst.localize(datetime(
                (local_dt - timedelta(days=185)).year,
                (local_dt - timedelta(days=185)).month,
                (local_dt - timedelta(days=185)).day,
                local_dt.hour
            )))
            t1 = ts.from_datetime(local_dt)
            
            # 이분이지 이벤트 검색 (0:춘분, 1:하지, 2:추분, 3:동지)
            t_events, y_events = almanac.find_discrete(t0, t1, almanac.seasons(eph))
            
            if len(t_events) > 0:
                last_event_index = y_events[-1]
                last_event_time = t_events[-1].astimezone(kst)
                
                season_names = {0: "춘분", 1: "하지", 2: "추분", 3: "동지"}
                output_mapping = {0: "춘분이후", 1: "하지이후", 2: "추분이후", 3: "동지이후"}
                
                current_season = season_names[last_event_index]
                result_period = output_mapping[last_event_index]
                
                # --- 결과 출력 화면 ---
                st.success(f"### 판별 결과: **{result_period}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="입력된 기준 시각", value=local_dt.strftime('%Y-%m-%d %H:%M'))
                with col2:
                    st.metric(label="가장 가까운 직전 절기", value=f"{current_season}")
                
                st.info(f"💡 **참고:** 기준 시각 직전에 통과한 절기는 **{last_event_time.strftime('%Y-%m-%d %H:%M KST')}**에 절입된 **{current_season}**입니다.")
            else:
                st.error("지정된 범위 내에서 절입 시점을 찾을 수 없습니다. 입력 날짜를 확인해 주세요.")
                
        except Exception as e:
            st.error(f"계산 중 오류가 발생했습니다: {e}")
else:
    st.info("← 왼쪽 사이드바에서 날짜와 시간을 입력한 후 **[구간 판별하기]** 버튼을 눌러주세요.")