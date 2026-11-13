import numpy as np
import pandas as pd

POWER_MIN, POWER_MAX = 500, 700
PRESSURE_MIN, PRESSURE_MAX = 500, 900
TIME_MIN, TIME_MAX = 0.5, 3.0

P0 = 700.0  # RF Power 기준점 (W)
p0 = 500.0  # Pressure 기준점 (mTorr)
R0 = 377.0  # 기준 식각 속도 (nm/min)


def calculate_etch_rate(power: float, pressure: float) -> float:
    """2차 가산형 보간 모델 기반 식각 속도 계산 (nm/min)"""
    dP = power - P0
    dp = pressure - p0
    
    delta_R_P = 0.9595 * dP - 0.000235 * (dP ** 2)
    delta_R_p = -0.3205 * dp + 0.0002075 * (dp ** 2)
    
    rate = R0 + delta_R_P + delta_R_p
    return max(rate, 0.0)

def calculate_nonuniformity(power: float, pressure: float) -> float:
    """2차 가산형 보간 모델 기반 비균일도 계산 (%)"""
    x = (power - 700.0) / 100.0
    y = (pressure - 500.0) / 200.0
    
    nu = 3.9 + 3.4 * x + 2.3 * (x ** 2) - 1.45 * y + 0.75 * (y ** 2)
    return max(nu, 0.1)


def calculate_wafer_map(avg_depth: float, nonuniformity: float, grid_size: int = 11):
    """
    반경 방향 대칭 분포 모델을 적용한 가상 웨이퍼 깊이 맵 생성
    Di = D_bar * [1 - k(qi - q_bar)]
    """
    half = grid_size // 2
    depth_map = np.full((grid_size, grid_size), np.nan)
    mask = np.zeros((grid_size, grid_size), dtype=bool)
    q_values = np.zeros((grid_size, grid_size))
    q_list = []
    
    for i in range(grid_size):
        for j in range(grid_size):
            xi = (j - half) / half  # -1 ~ 1 정규화
            yi = (i - half) / half
            rho_sq = xi**2 + yi**2
            
            if rho_sq <= 1.0:  # 웨이퍼 영역 반경 내부
                mask[i, j] = True
                qi = rho_sq ** 2 
                q_values[i, j] = qi
                q_list.append(qi)
                
    if not q_list:
        return depth_map, mask
        
    q_bar = np.mean(q_list)
    q_min, q_max = np.min(q_list), np.max(q_list)

    k = (2.0 * (nonuniformity / 100.0)) / (q_max - q_min) if (q_max - q_min) > 0 else 0.0

    for i in range(grid_size):
        for j in range(grid_size):
            if mask[i, j]:
                depth_map[i, j] = avg_depth * (1.0 - k * (q_values[i, j] - q_bar))
                
    return depth_map, mask

def calculate_yield(depth_map, mask, target_depth: float = 600.0, tolerance: float = 20.0):
    """식각 깊이 규격 이내(Dtarget ± ΔD) 소자 비율 판정 및 수율 산출"""
    valid_depths = depth_map[mask]
    if len(valid_depths) == 0:
        return 0.0, 0, 0, np.array([])
        
    lower_limit = target_depth - tolerance
    upper_limit = target_depth + tolerance
    
    pass_mask = (valid_depths >= lower_limit) & (valid_depths <= upper_limit)
    n_pass = int(np.sum(pass_mask))
    n_total = len(valid_depths)
    yield_rate = (n_pass / n_total) * 100.0
    
    return yield_rate, n_pass, n_total, pass_mask

def run_grid_search(target_depth: float = 600.0, tolerance: float = 20.0):
    """
    RF Power (500~700 W), Pressure (500~900 mTorr), Time (0.5~3.0 min)
    총 2,106개 공정 조합 Grid Search 탐색
    """
    powers = np.arange(500, 725, 25)      
    pressures = np.arange(500, 950, 50)   
    times = np.round(np.arange(0.5, 3.1, 0.1), 1)  
    
    best_yield = -1.0
    best_diff = float('inf')
    best_config = None
    
    for P in powers:
        for p in pressures:
            rate = calculate_etch_rate(P, p)
            nu = calculate_nonuniformity(P, p)
            for t in times:
                avg_depth = rate * t
                d_map, mask = calculate_wafer_map(avg_depth, nu)
                y_rate, _, _, _ = calculate_yield(d_map, mask, target_depth, tolerance)
                
                diff = abs(avg_depth - target_depth)
                
                if (y_rate > best_yield) or (np.isclose(y_rate, best_yield) and diff < best_diff):
                    best_yield = y_rate
                    best_diff = diff
                    best_config = {
                        "Power": P,
                        "Pressure": p,
                        "Time": t,
                        "EtchRate": rate,
                        "AvgDepth": avg_depth,
                        "Nonuniformity": nu,
                        "Yield": y_rate
                    }
                    
    return best_config
