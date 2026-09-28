"""
결측치 단순 대체 시 '신뢰구간이 좁아져 참값을 놓치는 현상(과소포획)' 시각화
- [왼쪽] 정직한 데이터: 실제 분산이 반영되어 넉넉한 신뢰구간(95% 포획 성공)
- [오른쪽] 결측치를 평균으로 채운 데이터: 분산이 인위적으로 줄어들어 좁아진 신뢰구간(참값 놓침, 88%로 하락)
"""

import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def create_comparison_plot():
    np.random.seed(105)
    
    TRUE_MU = 175.0   # 진짜 참값: 175cm
    TRUE_SIGMA = 6.0
    N = 30
    NUM_TRIALS = 40   # 한눈에 비교하기 좋게 40회 시뮬레이션
    
    # 데이터 생성
    normal_intervals = []
    normal_means = []
    normal_hits = []
    
    imputed_intervals = []
    imputed_means = []
    imputed_hits = []
    
    for _ in range(NUM_TRIALS):
        # 1. 원본 정상 표본 (N=30)
        sample_true = np.random.normal(TRUE_MU, TRUE_SIGMA, N)
        mean_t = np.mean(sample_true)
        se_t = np.std(sample_true, ddof=1) / np.sqrt(N)
        ci_t = (mean_t - 1.96 * se_t, mean_t + 1.96 * se_t)
        hit_t = (ci_t[0] <= TRUE_MU <= ci_t[1])
        
        normal_intervals.append(ci_t)
        normal_means.append(mean_t)
        normal_hits.append(hit_t)
        
        # 2. 결측치 40% 발생 후 단순 평균으로 채운 표본 (나쁜 예시)
        # 30개 중 12개를 지우고 나머지 18개의 평균으로 12개를 똑같이 채움
        sample_missing = sample_true.copy()
        observed = sample_missing[:18]
        obs_mean = np.mean(observed)
        # 결측된 12자리에 obs_mean을 복사-붙여넣기
        sample_imputed = np.concatenate([observed, np.full(12, obs_mean)])
        
        mean_i = np.mean(sample_imputed)
        # 결측치를 똑같은 값으로 채워 넣었기 때문에 표준편차가 확 줄어듦!
        se_i = np.std(sample_imputed, ddof=1) / np.sqrt(N)
        ci_i = (mean_i - 1.96 * se_i, mean_i + 1.96 * se_i)
        hit_i = (ci_i[0] <= TRUE_MU <= ci_i[1])
        
        imputed_intervals.append(ci_i)
        imputed_means.append(mean_i)
        imputed_hits.append(hit_i)
        
    normal_acc = sum(normal_hits) / NUM_TRIALS * 100
    imputed_acc = sum(imputed_hits) / NUM_TRIALS * 100
    
    # 시각화 (좌우 2개 서브플롯)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 9), sharey=True)
    
    # [왼쪽] 정상적인 경우
    for i in range(NUM_TRIALS):
        low, up = normal_intervals[i]
        m = normal_means[i]
        hit = normal_hits[i]
        color = '#1f77b4' if hit else '#d62728'
        lw = 1.2 if hit else 2.5
        ax1.plot([low, up], [i+1, i+1], color=color, linewidth=lw, alpha=0.85)
        ax1.scatter(m, i+1, color=color, s=15, zorder=3)
        
    ax1.axvline(x=TRUE_MU, color='black', linestyle='--', linewidth=2, label=f'진짜 참값 ({TRUE_MU}cm)')
    ax1.set_title(f'1. 정상 데이터 (정직한 그물)\n성공률: {normal_acc:.1f}% (그물이 넉넉함)', fontsize=13, fontweight='bold', color='#1f77b4')
    ax1.set_xlabel('신뢰구간 범위 (cm)', fontsize=11)
    ax1.set_ylabel('조사 회차 (1~40)', fontsize=11)
    ax1.set_xlim(168, 182)
    ax1.grid(True, linestyle=':', alpha=0.5)
    ax1.legend(loc='upper right')
    
    # [오른쪽] 결측치를 단순 평균으로 채운 경우
    for i in range(NUM_TRIALS):
        low, up = imputed_intervals[i]
        m = imputed_means[i]
        hit = imputed_hits[i]
        color = '#1f77b4' if hit else '#d62728'
        lw = 1.2 if hit else 2.5
        ax2.plot([low, up], [i+1, i+1], color=color, linewidth=lw, alpha=0.85)
        ax2.scatter(m, i+1, color=color, s=15, zorder=3)
        
    ax2.axvline(x=TRUE_MU, color='black', linestyle='--', linewidth=2, label=f'진짜 참값 ({TRUE_MU}cm)')
    ax2.set_title(f'2. 결측치 평균 대체 (너무 좁아진 그물)\n성공률: {imputed_acc:.1f}% (빨간색 실패 폭증!)', fontsize=13, fontweight='bold', color='#d62728')
    ax2.set_xlabel('신뢰구간 범위 (cm)', fontsize=11)
    ax2.set_xlim(168, 182)
    ax2.grid(True, linestyle=':', alpha=0.5)
    ax2.legend(loc='upper right')
    
    fig.suptitle('왜 결측치를 평균으로 채우면 참값을 놓치게 될까? (그물 크기 비교)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    out_dir = r"D:\SourceBank\ai-vibecoding-2026\output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "undercoverage_explained.png")
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"이미지 저장 완료: {out_path}")

if __name__ == "__main__":
    create_comparison_plot()
