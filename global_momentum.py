# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Global Full-Country Momentum",
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
  <h1>Global Country ETF Radar</h1>
  <p>전 세계 46개 국가 iShares ETF 실시간 전수 조사 및 모멘텀 분석</p>
</div>
""", unsafe_allow_html=True)

# ── 국가별 ETF 전수 라인업 (46개국) ───────────────────────────
COUNTRY_ETFS = {
    # 미주 (7)
    'IVV': '미국', 'EWC': '캐나다', 'EWW': '멕시코', 'EWZ': '브라질', 'ECH': '칠레', 'EPU': '페루', 'ARGT': '아르헨티나',
    # 아시아/오세아니아 (12)
    'EWY': '한국', 'EWJ': '일본', 'MCHI': '중국', 'EWT': '대만', 'INDA': '인도', 'EWA': '호주', 'ENZL': '뉴질랜드', 
    'EWS': '싱가포르', 'EWM': '말레이시아', 'THD': '태국', 'EIDO': '인도네시아', 'EPHE': '필리핀',
    # 서유럽/남유럽 (9)
    'EWG': '독일', 'EWU': '영국', 'EWQ': '프랑스', 'EWI': '이탈리아', 'EWP': '스페인', 'EWL': '스위스', 
    'EWN': '네덜란드', 'EWK': '벨기에', 'EIRL': '아일랜드',
    # 북유럽/동유럽 (8)
    'EWD': '스웨덴', 'EDEN': '덴마크', 'ENOR': '노르웨이', 'EFNL': '핀란드', 'EWO': '오스트리아', 
    'EPOL': '폴란드', 'GREK': '그리스', 'PGAL': '포르투갈',
    # 중동/아프리카 (10)
    'EIS': '이스라엘', 'TUR': '튀르키예', 'EZA': '남아프리카공화국', 'KSA': '사우디아라비아', 
    'QAT': '카타르', 'UAE': '아랍에미리트', 'EGPT': '이집트', 'KWT': '쿠웨이트', 'NGE': '나이지리아', 'AFK': '아프리카전체'
}

# ── 모멘텀 계산 함수 ──────────────────────────────────────────
def avg_momentum(series):
    s = series.dropna()
    if len(s) < 13: return np.nan, np.nan, np.nan, np.nan, np.nan
    p = s.iloc[-1]
    r1, r3, r6, r12 = p/s.iloc[-2]-1, p/s.iloc[-4]-1, p/s.iloc[-7]-1, p/s.iloc[-13]-1
    return (r1+r3+r6+r12)/4, r1, r3, r6, r12

# ── 실행 로직 ─────────────────────────────────────────────────
if st.button("🚀 전 세계 46개국 모멘텀 전수 조사 시작", type="primary"):
    with st.status("글로벌 데이터 수집 및 분석 중...", expanded=True) as status:
        tickers = list(COUNTRY_ETFS.keys())
        st.write(f"📡 {len(tickers)}개국 데이터를 수집합니다. 잠시만 기다려 주세요...")
        
        end = datetime.today()
        start = end - timedelta(days=430)
        
        # 주가 다운로드
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
                    rows.append({
                        '티커': tk, 
                        '국가': COUNTRY_ETFS[tk], 
                        '평균모멘텀(%)': round(m*100, 2), 
                        '1M': round(r1*100, 2), 
                        '3M': round(r3*100, 2), 
                        '6M': round(r6*100, 2), 
                        '12M': round(r12*100, 2)
                    })
        
        df = pd.DataFrame(rows).sort_values('평균모멘텀(%)', ascending=False).reset_index(drop=True)
        df.index += 1
        status.update(label="전 세계 분석 완료!", state="complete")

    st.divider()
    
    # 상단 정보 카드
    c1, c2, c3 = st.columns(3)
    tip_txt = f"{tip_avg*100:+.2f}%" if not np.isnan(tip_avg) else "N/A"
    c1.markdown(f'<div class="metric-box"><div style="font-size:0.75rem; color:#1e3a8a;">글로벌 거시 필터(TIP)</div><div style="font-size:1.5rem; font-weight:600;">{tip_txt}</div><div style="margin-top:5px;">{"<span class='tag-pass'>PASS</span>" if tip_pass else "<span style='background:#fee2e2; color:#b91c1c; padding:2px 10px; border-radius:99px; font-size:0.8rem; font-weight:600;'>BLOCK</span>"}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div style="font-size:0.75rem; color:#1e3a8a;">분석 국가 수</div><div style="font-size:1.5rem; font-weight:600;">{len(df)}개국</div><div style="margin-top:5px; font-size:0.8rem; color:#64748b;">iShares Full Lineup</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div style="font-size:0.75rem; color:#1e3a8a;">마지막 업데이트</div><div style="font-size:1.5rem; font-weight:600;">{datetime.today().strftime("%m/%d")}</div><div style="margin-top:5px; font-size:0.8rem; color:#64748b;">실시간 데이터 기준</div></div>', unsafe_allow_html=True)

    if not tip_pass:
        st.error("⚠️ TIP 필터 차단: 글로벌 시장의 위험이 감지되었습니다. 현금(달러) 보유가 유리할 수 있습니다.")
    elif not df.empty:
        best = df.iloc[0]
        st.markdown(f"""
        <div class="winner-card">
          <div style="font-size:0.8rem; color:#166534; text-transform:uppercase; letter-spacing:0.1em;">이번 달 글로벌 TOP 1</div>
          <div class="ticker">{best['티커']}</div>
          <div class="name">{best['국가']} 증시</div>
          <div style="font-size:1.3rem; font-weight:600; color:#15803d; margin-top:10px;">평균 모멘텀 스코어: {best['평균모멘텀(%)']:+.2f}%</div>
          <div style="font-size:0.85rem; color:#4d7c0f; margin-top:8px;">1M: {best['1M']}% | 3M: {best['3M']}% | 6M: {best['6M']}% | 12M: {best['12M']}%</div>
        </div>""", unsafe_allow_html=True)
        
        st.subheader("🏆 전 세계 국가별 모멘텀 순위 (전수 조사)")
        st.dataframe(df.style.background_gradient(cmap='RdYlGn', subset=['평균모멘텀(%)']), use_container_width=True, height=600)
