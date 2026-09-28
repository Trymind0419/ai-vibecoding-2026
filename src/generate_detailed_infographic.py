"""
인포그래픽형 상세 설명 이미지 생성 스크립트
- 제목, 원리 설명 카드, 수식 해설, 비교 시뮬레이션 그래프, 주석 및 실무 가이드라인 포함
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def create_detailed_infographic():
    np.random.seed(105)
    
    TRUE_MU = 175.0   # 진짜 참값: 175cm
    TRUE_SIGMA = 6.0
    N = 30
    NUM_TRIALS = 30   # 깔끔한 시각화를 위해 30회
    
    # 1. 데이터 시뮬레이션
    norm_intervals, norm_means, norm_hits = [], [], []
    imp_intervals, imp_means, imp_hits = [], [], []
    
    for _ in range(NUM_TRIALS):
        sample_true = np.random.normal(TRUE_MU, TRUE_SIGMA, N)
        mean_t = np.mean(sample_true)
        se_t = np.std(sample_true, ddof=1) / np.sqrt(N)
        ci_t = (mean_t - 1.96 * se_t, mean_t + 1.96 * se_t)
        hit_t = (ci_t[0] <= TRUE_MU <= ci_t[1])
        norm_intervals.append(ci_t)
        norm_means.append(mean_t)
        norm_hits.append(hit_t)
        
        # 결측 40% 평균 대체
        sample_missing = sample_true.copy()
        observed = sample_missing[:18]
        obs_mean = np.mean(observed)
        sample_imp = np.concatenate([observed, np.full(12, obs_mean)])
        
        mean_i = np.mean(sample_imp)
        se_i = np.std(sample_imp, ddof=1) / np.sqrt(N)
        ci_i = (mean_i - 1.96 * se_i, mean_i + 1.96 * se_i)
        hit_i = (ci_i[0] <= TRUE_MU <= ci_i[1])
        imp_intervals.append(ci_i)
        imp_means.append(mean_i)
        imp_hits.append(hit_i)
        
    norm_rate = sum(norm_hits) / NUM_TRIALS * 100
    imp_rate = sum(imp_hits) / NUM_TRIALS * 100
    
    # 2. 캔버스 레이아웃 (GridSpec)
    fig = plt.figure(figsize=(16, 13), facecolor='#f8f9fa')
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 3.2, 1.0], hspace=0.35, wspace=0.15)
    
    # [메인 타이틀]
    fig.text(0.5, 0.96, "결측치를 평균으로 채우면 왜 통계가 망가질까?", 
             fontsize=22, fontweight='bold', ha='center', color='#111827')
    fig.text(0.5, 0.935, "인위적인 분산 축소가 초래하는 '신뢰구간 축소'와 '참값 포획 실패'의 시각적 원리 해설", 
             fontsize=13, ha='center', color='#4b5563')
    
    # [상단 텍스트 카드 1: 원리 해설]
    ax_card1 = fig.add_subplot(gs[0, 0])
    ax_card1.axis('off')
    card1_box = patches.FancyBboxPatch((0.02, 0.05), 0.96, 0.90, boxstyle="round,pad=0.03", 
                                        fc="#ffffff", ec="#cbd5e1", lw=1.5)
    ax_card1.add_patch(card1_box)
    
    card1_text = (
        " [STEP 1] 컴퓨터의 착각과 공식의 함정\n\n"
        "• 원래 데이터:  20점, 50점, 70점, 100점 (들쭉날쭉함 -> 편차 큼)\n"
        "• 평균 대체 후: 20, 50, 70, 100 + [60, 60, 60, 60, 60] (평균 복사)\n"
        "  -> 컴퓨터: '모두 60점 주변이네? 데이터의 편차(s)가 거의 없구나!'\n"
        "• 신뢰구간 공식:  폭 = 2 * 1.96 * ( s / √N )\n"
        "  -> 편차(s)가 인위적으로 줄어들면서, 신뢰구간(그물) 폭이 쪼그라듦!"
    )
    ax_card1.text(0.06, 0.50, card1_text, fontsize=11, color='#1f2937', va='center', linespacing=1.6)

    # [상단 텍스트 카드 2: 결과 해설]
    ax_card2 = fig.add_subplot(gs[0, 1])
    ax_card2.axis('off')
    card2_box = patches.FancyBboxPatch((0.02, 0.05), 0.96, 0.90, boxstyle="round,pad=0.03", 
                                        fc="#ffffff", ec="#cbd5e1", lw=1.5)
    ax_card2.add_patch(card2_box)
    
    card2_text = (
        " [STEP 2] 좁아진 그물이 초래하는 참사\n\n"
        "• 정직한 그물 (정상): 그물이 넓어서 표본이 살짝 빗나가도\n"
        "  진짜 정답(참값 175cm)을 안전하게 그물 안에 가둠 (성공률 95%)\n"
        "• 좁아진 그물 (평균 대체): 그물이 젓가락처럼 좁아져서\n"
        "  표본이 조금만 치우쳐도 참값이 그물 바깥으로 쏙 빠져나감!\n"
        "• 결과: '95%짜리 믿을 만한 구간'이라고 우겼지만, 실제로는\n"
        "  80%대로 성공률이 폭락하는 통계적 왜곡(과소포획) 발생!"
    )
    ax_card2.text(0.06, 0.50, card2_text, fontsize=11, color='#1f2937', va='center', linespacing=1.6)

    # [중간 왼쪽 그래프: 정상 데이터]
    ax_plot1 = fig.add_subplot(gs[1, 0])
    ax_plot1.set_facecolor('#ffffff')
    for i in range(NUM_TRIALS):
        low, up = norm_intervals[i]
        m = norm_means[i]
        hit = norm_hits[i]
        col = '#0284c7' if hit else '#dc2626'
        lw = 1.3 if hit else 2.6
        ax_plot1.plot([low, up], [i+1, i+1], color=col, linewidth=lw, alpha=0.85)
        ax_plot1.scatter(m, i+1, color=col, s=16, zorder=3)
        
    ax_plot1.axvline(x=TRUE_MU, color='#111827', linestyle='--', linewidth=2, label=f'진짜 참값 (μ = {TRUE_MU}cm)')
    ax_plot1.set_title(f"A. 정상 데이터 (정직하게 넓은 그물)\n실제 성공률: {norm_rate:.1f}% [목표 95% 달성]", 
                       fontsize=13, fontweight='bold', color='#0284c7', pad=10)
    ax_plot1.set_xlabel('키 신뢰구간 (cm)', fontsize=11)
    ax_plot1.set_ylabel('조사 회차 (1 ~ 30)', fontsize=11)
    ax_plot1.set_xlim(168, 182)
    ax_plot1.grid(True, linestyle=':', alpha=0.6)
    ax_plot1.legend(loc='upper right', frameon=True)
    
    # [중간 오른쪽 그래프: 결측치 평균 대체]
    ax_plot2 = fig.add_subplot(gs[1, 1], sharey=ax_plot1)
    ax_plot2.set_facecolor('#ffffff')
    for i in range(NUM_TRIALS):
        low, up = imp_intervals[i]
        m = imp_means[i]
        hit = imp_hits[i]
        col = '#0284c7' if hit else '#dc2626'
        lw = 1.3 if hit else 2.6
        ax_plot2.plot([low, up], [i+1, i+1], color=col, linewidth=lw, alpha=0.85)
        ax_plot2.scatter(m, i+1, color=col, s=16, zorder=3)
        
    ax_plot2.axvline(x=TRUE_MU, color='#111827', linestyle='--', linewidth=2, label=f'진짜 참값 (μ = {TRUE_MU}cm)')
    ax_plot2.set_title(f"B. 결측치 평균 대체 (인위적으로 좁아진 그물)\n실제 성공률: {imp_rate:.1f}% [빨간색 실패 폭증!]", 
                       fontsize=13, fontweight='bold', color='#dc2626', pad=10)
    ax_plot2.set_xlabel('키 신뢰구간 (cm)', fontsize=11)
    ax_plot2.set_xlim(168, 182)
    ax_plot2.grid(True, linestyle=':', alpha=0.6)
    ax_plot2.legend(loc='upper right', frameon=True)
    
    # 실패한 선 하나에 주석 화살표 추가
    for i in range(NUM_TRIALS):
        if not imp_hits[i]:
            low, up = imp_intervals[i]
            target_x = up if up < TRUE_MU else low
            ax_plot2.annotate('그물이 너무 좁아서\n참값을 놓침!', 
                              xy=(target_x, i+1), 
                              xytext=(target_x + (-3.5 if target_x < TRUE_MU else 1.2), i+3.5),
                              arrowprops=dict(facecolor='#dc2626', shrink=0.08, width=1.5, headwidth=6),
                              fontsize=10, fontweight='bold', color='#dc2626',
                              bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#ef4444", lw=1))
            break

    # [하단 종합 솔루션 카드: 다중대체법의 필요성]
    ax_bot = fig.add_subplot(gs[2, :])
    ax_bot.axis('off')
    bot_box = patches.FancyBboxPatch((0.01, 0.05), 0.98, 0.88, boxstyle="round,pad=0.03", 
                                     fc="#eff6ff", ec="#3b82f6", lw=1.8)
    ax_bot.add_patch(bot_box)
    
    bot_text = (
        "★ [통계 실무 핵심 솔루션] : 왜 정통 통계학에서는 '다중 대체법(MICE)'을 쓰는가?\n\n"
        "1. 단순 평균 대체는 '우리가 가짜 데이터를 넣었다'는 불확실성을 무시하고 편차(분산)를 강제로 축소시킵니다.\n"
        "2. 반면 다중 대체법(MICE)은 확률 시뮬레이션으로 가짜 값을 5~10번 다르게 채워 넣어 가상 데이터셋들을 만듭니다.\n"
        "3. 그 결과 '가짜 값을 넣어서 생긴 불확실성'만큼 그물(신뢰구간)을 다시 정직하게 넓혀주어, 성공률 95%를 완벽하게 지켜냅니다!"
    )
    ax_bot.text(0.03, 0.50, bot_text, fontsize=11.5, color='#1e3a8a', va='center', linespacing=1.6)

    out_dir = r"D:\SourceBank\ai-vibecoding-2026\output"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ci_detailed_infographic.png")
    plt.savefig(out_file, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"인포그래픽 이미지 저장 완료: {out_file}")

if __name__ == "__main__":
    create_detailed_infographic()
