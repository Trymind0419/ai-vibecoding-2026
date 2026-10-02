# [작업 계획] 최대 보유 종목 수 7개 확대 (자유 매매 지원)

## 1. 개요 및 목적
- 기존 최대 3개로 제한되어 있던 동시 보유 종목 수를 최대 7개로 상향 조정
- 다양한 주도주 및 급등주에 대해 보다 자유롭고 유연한 분산 자동매매가 이루어지도록 설정 및 로직 업데이트

## 2. 세부 변경 작업
- [x] `auto_trader/config.py`: `MAX_POSITIONS` 환경 설정 필드(기본값 7) 추가
- [x] `.env`: `MAX_POSITIONS=7` 환경변수 항목 추가 및 가이드 주석 반영
- [x] `auto_trader/strategy.py`: `MASTER_STRATEGY_CONFIG` 및 전략 인스턴스의 `max_positions` 기본값을 3에서 7로 변경 (settings 연동)
- [x] `auto_trader/main.py`: `BotSettingsUpdateRequest`에 `max_positions` 필드 추가 및 실시간 봇 설정 업데이트 API 지원
- [x] 동작 및 문법 검증: python 컴파일 및 임포트 검증

## 3. 결과 및 확인
- 봇이 최대 7종목까지 자유롭게 진입 가능함을 보장
- 단일 종목 40% 자산 상한 및 리스크 관리(손절/익절/트레일링 스탑)는 기존대로 안전하게 유지
