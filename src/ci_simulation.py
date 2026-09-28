"""
신뢰구간(Confidence Interval) 100회 시뮬레이션
- 모집단 참값(진짜 평균 키): mu = 175.0 cm, sigma = 6.0 cm
- 표본 크기: n = 30명
- 조사 횟수: 100회 반복
- 신뢰수준: 95% (z = 1.96)
"""

import os
import numpy as np
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_simulation(seed=42):
    np.random.seed(seed)
    
    # 1. 모집단의 진짜 참값 설정
    TRUE_MU = 175.0   # 국민 진짜 평균 키: 175cm (참값)
    TRUE_SIGMA = 6.0  # 모표준편차
    SAMPLE_SIZE = 30  # 1회 조사당 표본 크기 (30명)
    NUM_TRIALS = 100  # 조사 반복 횟수 (100회)
    Z_VAL = 1.96      # 95% 신뢰수준의 임계값
    
    success_count = 0
    failure_count = 0
    
    intervals = []
    sample_means = []
    is_contained = []
    
    # 2. 100번의 독립적인 표본 조사 시뮬레이션
    for i in range(NUM_TRIALS):
        # 30명의 표본 무작위 추출
        sample = np.random.normal(loc=TRUE_MU, scale=TRUE_SIGMA, size=SAMPLE_SIZE)
        
        sample_mean = np.mean(sample)
        sample_std = np.std(sample, ddof=1) # 표본표준편차
        
        # 표준오차 (Standard Error)
        se = sample_std / np.sqrt(SAMPLE_SIZE)
        
        # 95% 신뢰구간 계산: [표본평균 - 1.96*SE, 표본평균 + 1.96*SE]
        ci_lower = sample_mean - Z_VAL * se
        ci_upper = sample_mean + Z_VAL * se
        
        # 참값(175.0)이 신뢰구간 안에 들어가는지 확인
        contained = (ci_lower <= TRUE_MU <= ci_upper)
        
        if contained:
            success_count += 1
        else:
            failure_count += 1
            
        intervals.append((ci_lower, ci_upper))
        sample_means.append(sample_mean)
        is_contained.append(contained)

    # 3. 콘솔 결과 출력
    print("=" * 60)
    print("      [95% 신뢰구간 100회 반복 시뮬레이션 결과]      ")
    print("=" * 60)
    print(f"- 모집단 진짜 참값(평균 키) : {TRUE_MU:.1f} cm")
    print(f"- 각 조사당 표본 크기       : {SAMPLE_SIZE} 명")
    print(f"- 총 조사 반복 횟수         : {NUM_TRIALS} 회")
    print(f"- 참값 포획 성공(구간 내 포함): {success_count} 회 ({success_count}%)")
    print(f"- 참값 포획 실패(빗나간 구간): {failure_count} 회 ({failure_count}%)")
    print("-" * 60)
    
    print("\n[실패한(참값을 놓친) 회차 상세]:")
    for idx, (contained, (low, up), m) in enumerate(zip(is_contained, intervals, sample_means), 1):
        if not contained:
            print(f"  - 제 {idx:3d}회차: 표본평균={m:.2f}cm, 95% CI=[{low:.2f} ~ {up:.2f}cm] -> [실패] 참값(175.0) 놓침!")
            
    print("\n[성공한 회차 중 샘플 3건]:")
    sampled_success = [(idx, m, low, up) for idx, (c, (low, up), m) in enumerate(zip(is_contained, intervals, sample_means), 1) if c][:3]
    for idx, m, low, up in sampled_success:
        print(f"  - 제 {idx:3d}회차: 표본평균={m:.2f}cm, 95% CI=[{low:.2f} ~ {up:.2f}cm] -> [성공] 참값(175.0) 포함")
    print("=" * 60)

    # 4. 시각화 그래프 작성 및 저장
    plt.figure(figsize=(10, 12))
    
    for i in range(NUM_TRIALS):
        low, up = intervals[i]
        mean = sample_means[i]
        contained = is_contained[i]
        
        # 성공: 파란색 선, 실패: 굵은 빨간색 선
        color = '#1f77b4' if contained else '#d62728'
        linewidth = 1.0 if contained else 2.5
        alpha = 0.6 if contained else 1.0
        
        plt.plot([low, up], [i+1, i+1], color=color, linewidth=linewidth, alpha=alpha)
        plt.scatter(mean, i+1, color=color, s=10 if contained else 25, zorder=3)

    # 참값(175.0cm) 수직 기준선
    plt.axvline(x=TRUE_MU, color='black', linestyle='--', linewidth=2, label=f'진짜 참값 (μ = {TRUE_MU}cm)')
    
    # 커스텀 범례 생성
    plt.plot([], [], color='#1f77b4', linewidth=1.5, label=f'성공 구간: {success_count}회 ({success_count}%)')
    plt.plot([], [], color='#d62728', linewidth=2.5, label=f'실패(빗나감) 구간: {failure_count}회 ({failure_count}%)')
    
    plt.title(f'95% 신뢰구간 100회 시뮬레이션 (성공률: {success_count}%)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('신뢰구간 범위 및 표본평균 (cm)', fontsize=12)
    plt.ylabel('조사 회차 (1 ~ 100번째)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.legend(loc='upper right', frameon=True, shadow=True, fontsize=11)
    plt.tight_layout()
    
    output_dir = r"D:\SourceBank\ai-vibecoding-2026\output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ci_simulation_result.png")
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"\n[그래프 이미지 저장 완료]: {output_path}")

if __name__ == "__main__":
    run_simulation()
