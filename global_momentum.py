# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Global Country Momentum",
    page_icon="🌍",
    layout="wide"
)

# ── CSS 디자인 ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.title-block { border-left: 4px solid #3b82f6; padding: 0.4rem 1rem; margin-bottom: 1.5rem; }
.title-block h1 { font-size: 1.6rem; font-weight: 600; margin: 0; }
.metric-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 1rem; text-align: center; }
.winner-card { background: #f0fdf4; border: 2px solid #22c55e; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; }
.winner-card .ticker { font-size: 2.5rem; font-weight: 600; color: #166534; font-family: 'IBM Plex Mono', monospace; }
.tag-pass { background: #dcfce7; color: #15803d; padding: 2px 10px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
  <h1>iShares Country ETF Momentum Picker</h1>
  <p>iShares 전 세계 국가별 ETF 라인업 실시간 스캔 및 모멘텀 분석</p>
</div>
""", unsafe_allow_html=True)

# ── 모멘텀 계산 함수 ──────────────────────────────────────────
def avg_momentum(series):
    s = series.dropna()
    if len(s) < 13: return np.nan, np.nan, np.nan, np.nan, np.nan
    p = s.iloc[-1]
    r1, r3, r6, r12 = p/s.iloc[-2]-1, p/s.iloc[-4]-1, p/s.iloc[-7]-1, p/s.iloc[-13]-1
    return (r1+r3+r6+r12)/4, r1, r3, r6, r12

# ── 실시간 국가 ETF 스크래핑 ──────────────────────────────────
@st.cache_data(ttl=86400)
def get_all_country_etfs():
    scraped_dict = {}
    try:
        # 위키피디아 iShares 리스트 페이지
        url = "https://en.wikipedia.org/wiki/List_of_iShares_ETFs"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        tables = pd.read_html(resp.text)
        
        for t in tables:
            cols = [str(c).lower() for c in t.columns]
            if any('ticker' in c for c in cols) and any('country' in c or 'market' in c for c in cols):
                t_col = next(c for c in t.columns if 'ticker' in str(c).lower())
                n_col = next(c for c in t.columns if 'country' in str(c).lower() or 'market' in str(c).lower())
                for _, row in t.iterrows():
                    tk, nm = str(row[t_col]).strip(), str(row[n_col]).strip()
                    if len(tk) <= 4 and tk.isalpha() and 'world' not in nm.lower():
                        scraped_dict[tk] = nm
    except: pass
    
    # 폴백 (스크래핑 실패 대비 핵심 국가)
    fallback = {'IVV':'미국','EWY':'한국','EWJ':'일본','MCHI':'중국','EWG':'독일','EWU':'영국','INDA':'인도','EWT':'대만','EWC':'캐나다','EWA':'호주','EWZ':'브라질'}
    return (list(scraped_dict.keys()), scraped_dict) if len(scraped_dict) > 10 else (list(fallback.keys()), fallback)

# ── 실행 로직 ─────────────────────────────────────────────────
if st.button("🚀 전 세계 국가 모멘텀 분석 시작", type="primary"):
    with st.status("데이터 분석 중...", expanded=True) as status:
        tickers, name_map = get_all_country_etfs()
        st.write(f"✅ {len(tickers)}개 국가 ETF 라인업 확인 완료")
        
        end = datetime.today()
        start = end - timedelta(days=430)
        raw = yf.download(tickers + ['TIP'], start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True, progress=False)
        prices = raw['Close'] if isinstance(raw.columns, pd.MultiIndex) else raw[['Close']]
        monthly = prices.resample('ME').last()
        
        # TIP 필터
        tip_avg, _, _, _, _ = avg_momentum(monthly['TIP'])
        tip_pass = not np.isnan(tip_avg) and tip_avg > 0
        
        rows = []
        for tk in tickers:
            if tk in monthly.columns:
                m, r1, r3, r6, r12 = avg_momentum(monthly[tk])
                if not np.isnan(m):
                    rows.append({'티커': tk, '국가': name_map.get(tk, tk), '평균모멘텀(%)': round(m*100, 2), '1M': round(r1*100, 2), '3M': round(r3*100, 2), '6M': round(r6*100, 2), '12M': round(r12*100, 2)})
        
        df = pd.DataFrame(rows).sort_values('평균모멘텀(%)', ascending=False).reset_index(drop=True)
        df.index += 1
        status.update(label="분석 완료!", state="complete")

    st.divider()
    if not tip_pass:
        st.error("⚠️ TIP 필터 차단: 현재 글로벌 시장이 하락 추세입니다. 현금 보유를 권장합니다.")
    elif not df.empty:
        best = df.iloc[0]
        st.markdown(f"""
        <div class="winner-card">
          <div style="font-size:0.8rem; color:#166534;">이번 달 추천 국가</div>
          <div class="ticker">{best['티커']}</div>
          <div class="name">{best['국가']}</div>
          <div style="font-size:1.2rem; font-weight:600; color:#15803d; margin-top:10px;">평균 모멘텀: {best['평균모멘텀(%)']:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
