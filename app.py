import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from etch_model import (
    POWER_MIN, POWER_MAX, PRESSURE_MIN, PRESSURE_MAX, TIME_MIN, TIME_MAX,
    calculate_etch_rate, calculate_nonuniformity,
    calculate_wafer_map, calculate_yield, run_grid_search
)

st.set_page_config(
    page_title="SiO2 Etch Process Simulator & Yield Optimizer",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ SiO2 Etch Process Simulator & Virtual Yield Optimizer")
st.caption("Experimental Data-Based SiO2 Etching Process Analysis & Optimization (Capstone Design)")

st.sidebar.header("🛠️ 1. 공정 조건")
power = st.sidebar.slider("RF Power (W)", POWER_MIN, POWER_MAX, 650, 25)
pressure = st.sidebar.slider("Chamber Pressure (mTorr)", PRESSURE_MIN, PRESSURE_MAX, 600, 50)
etch_time = st.sidebar.slider("Etching Time (min)", TIME_MIN, TIME_MAX, 2.0, 0.1)

st.sidebar.divider()
st.sidebar.header("🎯 2. 목표 규격")
target_depth = st.sidebar.number_input("Target Depth Dtarget (nm)", value=600.0, step=10.0)
tolerance = st.sidebar.number_input("Tolerance ±ΔD (nm)", value=20.0, step=5.0)

etch_rate = calculate_etch_rate(power, pressure)
avg_depth = etch_rate * etch_time
nonuniformity = calculate_nonuniformity(power, pressure)
depth_map, mask = calculate_wafer_map(avg_depth, nonuniformity)
yield_rate, n_pass, n_total, pass_mask = calculate_yield(depth_map, mask, target_depth, tolerance)


tab1, tab2, tab3 = st.tabs(["📊 Step 1: 식각 모델링", "🗺️ Step 2: 웨이퍼 맵 & 가상 수율", "🔍 Step 3: Grid Search 최적화"])


with tab1:
    st.subheader("식각 속도 및 비균일도 2차 모델링")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Predicted Etch Rate (R)", f"{etch_rate:.2f} nm/min")
    col2.metric("Average Depth (D_bar)", f"{avg_depth:.2f} nm")
    col3.metric("Non-Uniformity (NU)", f"{nonuniformity:.2f} %")
    
    st.divider()
    
    #그래프 시각화
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Power Effect
    powers = np.linspace(POWER_MIN, POWER_MAX, 50)
    rates_p = [calculate_etch_rate(p, pressure) for p in powers]
    ax1.plot(powers, rates_p, 'b-', label=f'Pressure = {pressure} mTorr')
    ax1.scatter([power], [etch_rate], color='red', s=80, zorder=5, label='Current Point')
    ax1.set_title("RF Power vs Etch Rate")
    ax1.set_xlabel("RF Power (W)")
    ax1.set_ylabel("Etch Rate (nm/min)")
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()
    
    # Pressure Effect
    pressures = np.linspace(PRESSURE_MIN, PRESSURE_MAX, 50)
    rates_pr = [calculate_etch_rate(power, pr) for pr in pressures]
    ax2.plot(pressures, rates_pr, 'g-', label=f'RF Power = {power} W')
    ax2.scatter([pressure], [etch_rate], color='red', s=80, zorder=5, label='Current Point')
    ax2.set_title("Chamber Pressure vs Etch Rate")
    ax2.set_xlabel("Pressure (mTorr)")
    ax2.set_ylabel("Etch Rate (nm/min)")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()
    
    st.pyplot(fig)
    plt.close(fig)


with tab2:
    st.subheader("가상 웨이퍼 식각 깊이 분포 및 규격 판정")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("목표 규격 (Target)", f"{target_depth:.1f} ± {tolerance:.1f} nm")
    m2.metric("가상 수율 (Virtual Yield)", f"{yield_rate:.1f} %")
    m3.metric("정상 소자 (Pass)", f"{n_pass} / {n_total} 개")
    m4.metric("불량 소자 (Fail)", f"{n_total - n_pass} 개")
    
    col_map1, col_map2 = st.columns(2)
    
  
    with col_map1:
        fig_map, ax_map = plt.subplots(figsize=(5, 5))
        im = ax_map.imshow(depth_map, cmap='Blues', origin='upper')
        plt.colorbar(im, ax=ax_map, label='Etch Depth (nm)')
        ax_map.set_title(f"Wafer Depth Map (Avg: {avg_depth:.1f} nm)")
        ax_map.axis('off')
        st.pyplot(fig_map)
        plt.close(fig_map)
     
    with col_map2:
        pass_fail_map = np.full(depth_map.shape, np.nan)
        if mask.any():
            pass_fail_map[mask] = pass_mask.astype(float)
            
        fig_pf, ax_pf = plt.subplots(figsize=(5, 5))
        im_pf = ax_pf.imshow(pass_fail_map, cmap='RdYlGn', vmin=0, vmax=1, origin='upper')
        ax_pf.set_title(f"Pass/Fail Map (Yield: {yield_rate:.1f} %)")
        ax_pf.axis('off')
        st.pyplot(fig_pf)
        plt.close(fig_pf)


with tab3:
    st.subheader("Grid Search 기반 최적 조건 자동 탐색")
    st.write(f"탐색 범위: RF Power (500~700 W), Pressure (500~900 mTorr), Time (0.5~3.0 min) — 총 **2,106개** 조합 탐색")
    
    if st.button("🚀 Grid Search 최적화 실행하기", type="primary"):
        with st.spinner("2,106개 공정 조합을 계산 중입니다..."):
            best = run_grid_search(target_depth, tolerance)
            
        st.success("최적 공정 조건 탐색 완료!")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 📌 초기 조건 vs 최적화 조건 비교")
            comp_df = pd.DataFrame({
                "항목 (Item)": ["RF Power (W)", "Pressure (mTorr)", "Etching Time (min)", "Etch Rate (nm/min)", "평균 깊이 (nm)", "비균일도 (%)", "가상 수율 (%)"],
                "현재 설정값": [power, pressure, etch_time, f"{etch_rate:.2f}", f"{avg_depth:.2f}", f"{nonuniformity:.2f}", f"{yield_rate:.1f}%"],
                "최적화 조건": [best["Power"], best["Pressure"], best["Time"], f"{best['EtchRate']:.2f}", f"{best['AvgDepth']:.2f}", f"{best['Nonuniformity']:.2f}", f"{best['Yield']:.1f}%"]
            })
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            
        with c2:
            st.markdown("### 🎯 최적 조건 웨이퍼 맵 시각화")
            best_dmap, best_mask = calculate_wafer_map(best["AvgDepth"], best["Nonuniformity"])
            _, _, _, best_pmask = calculate_yield(best_dmap, best_mask, target_depth, tolerance)
            
            pf_best = np.full(best_dmap.shape, np.nan)
            pf_best[best_mask] = best_pmask.astype(float)
            
            fig_best, ax_best = plt.subplots(figsize=(4, 4))
            ax_best.imshow(pf_best, cmap='RdYlGn', vmin=0, vmax=1, origin='upper')
            ax_best.set_title(f"Optimized Yield: {best['Yield']:.1f} %")
            ax_best.axis('off')
            st.pyplot(fig_best)
            plt.close(fig_best)