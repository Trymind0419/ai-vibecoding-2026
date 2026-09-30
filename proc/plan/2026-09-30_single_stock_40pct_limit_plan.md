# SPARK Plan: 단일 종목 40% 비중 상한 로직 구현

## 작업 체크리스트
- [x] 전략 파라미터에 `max_stock_ratio_pct = 0.40` 추가 ([strategy.py](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/strategy.py))
- [x] 수량 계산 메서드 `calc_buy_qty`에 총자산 40% 한도 및 기존 보유액 차감 로직 반영 ([strategy.py](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/strategy.py))
- [x] 트레이더에 `get_total_assets` 구현 및 `order_buy` 발주 전 40% 상한 컷오프 안전장치 구축 ([nh_trader.py](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/nh_trader.py))
- [x] 자동매매봇 루프 `step`에서 총자산 기준 40% 이내 수량만 발주하도록 연동 ([bot.py](file:///d:/SourceBank/ai-vibecoding-2026/auto_trader/bot.py))
- [x] 단위 테스트 및 경계값 검증 완료
