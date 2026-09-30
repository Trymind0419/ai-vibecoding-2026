-- ==============================================================================
-- 🚀 auto_trader SQLite 전용 DBeaver 쿼리 모음집 (auto_trader_queries.sql)
-- 데이터베이스 파일 위치: D:\SourceBank\ai-vibecoding-2026\data\auto_trader.db
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. [핵심 요약] 가상계좌 자산 현황 (현금 + 주식 평가액 + 총 자산 + 총 수익률)
-- ------------------------------------------------------------------------------
SELECT * FROM v_account_summary;

-- (직접 계산 쿼리)
SELECT 
    a.paper_capital AS "예수금(현금 잔고)",
    COALESCE(SUM(p.qty * p.current_price), 0) AS "주식 평가금액",
    a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0) AS "총 평가자산",
    (a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0)) - a.initial_capital AS "누적 손익금",
    ROUND(((a.paper_capital + COALESCE(SUM(p.qty * p.current_price), 0) - a.initial_capital) * 100.0 / a.initial_capital), 2) || '%' AS "누적 수익률"
FROM account_state a
LEFT JOIN positions p ON 1=1
GROUP BY a.id;


-- ------------------------------------------------------------------------------
-- 2. [포트폴리오] 현재 보유 종목 현황 및 실시간 미실현 손익
-- ------------------------------------------------------------------------------
SELECT * FROM v_open_positions;

-- (커스텀 상세 쿼리)
SELECT 
    symbol AS "종목코드",
    name AS "종목명",
    qty AS "보유수량",
    CAST(buy_price AS INTEGER) AS "매수단가",
    CAST(current_price AS INTEGER) AS "현재가",
    CAST(highest_price AS INTEGER) AS "최고가(트레일링 기준)",
    CAST(qty * buy_price AS INTEGER) AS "매수총액",
    CAST(qty * current_price AS INTEGER) AS "평가금액",
    CAST(qty * (current_price - buy_price) AS INTEGER) AS "평가손익",
    ROUND(((current_price - buy_price) * 100.0 / buy_price), 2) || '%' AS "수익률",
    buy_time AS "매수일시"
FROM positions
ORDER BY buy_time DESC;


-- ------------------------------------------------------------------------------
-- 3. [거래일지] 청산 완료된 매매 내역 및 실현손익 (Closed Trades Journal)
-- ------------------------------------------------------------------------------
SELECT * FROM v_closed_trades_journal;

-- (승/패 필터링 및 상세 조회)
SELECT 
    id,
    symbol AS "종목코드",
    name AS "종목명",
    qty AS "수량",
    CAST(buy_price AS INTEGER) AS "매수가",
    CAST(sell_price AS INTEGER) AS "매도가",
    invested_amt AS "투자원금",
    revenue_amt AS "회수금액",
    realized_pnl AS "실현손익(원)",
    pnl_pct || '%' AS "수익률",
    CASE 
        WHEN realized_pnl > 0 THEN 'WIN (익절 🟢)'
        WHEN realized_pnl < 0 THEN 'LOSS (손절 🔴)'
        ELSE 'EVEN (본전 ⚪)'
    END AS "결과",
    exit_reason AS "청산사유",
    buy_time AS "매수일시",
    sell_time AS "청산일시"
FROM closed_trades
ORDER BY id DESC;


-- ------------------------------------------------------------------------------
-- 4. [종합 성과] 승률, 총 실현손익, 평균 수익률 집계
-- ------------------------------------------------------------------------------
SELECT * FROM v_trade_performance;

-- (상세 성과 지표)
SELECT 
    COUNT(*) AS "총 청산 거래건수",
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) AS "익절(승리) 건수",
    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) AS "손절(패배) 건수",
    ROUND(SUM(CASE WHEN realized_pnl > 0 THEN 1.0 ELSE 0.0 END) * 100.0 / MAX(COUNT(*), 1), 1) || '%' AS "승률(Win Rate)",
    SUM(realized_pnl) AS "누적 실현손익 총합(원)",
    SUM(invested_amt) AS "누적 총 투자원금(원)",
    ROUND(AVG(pnl_pct), 2) || '%' AS "건당 평균 수익률"
FROM closed_trades;


-- ------------------------------------------------------------------------------
-- 5. [일자별 성과] 일별 실현손익 & 거래건수 집계 (Daily Performance)
-- ------------------------------------------------------------------------------
SELECT * FROM v_daily_pnl_summary;


-- ------------------------------------------------------------------------------
-- 6. [종목별 성과] 어떤 종목에서 가장 많은 수익/손실이 발생했는가?
-- ------------------------------------------------------------------------------
SELECT 
    symbol AS "종목코드",
    name AS "종목명",
    COUNT(*) AS "거래횟수",
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) AS "승리",
    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) AS "패배",
    SUM(realized_pnl) AS "종목 총 실현손익(원)",
    ROUND(AVG(pnl_pct), 2) || '%' AS "평균 수익률"
FROM closed_trades
GROUP BY symbol, name
ORDER BY SUM(realized_pnl) DESC;


-- ------------------------------------------------------------------------------
-- 7. [주문 이력] 최근 체결/접수된 매수·매도 주문 로그 (Orders)
-- ------------------------------------------------------------------------------
SELECT 
    id,
    order_no AS "주문번호",
    time AS "주문시간",
    type AS "구분(BUY/SELL)",
    mode AS "모드(PAPER/LIVE)",
    symbol AS "종목코드",
    name AS "종목명",
    CAST(price AS INTEGER) AS "주문단가",
    qty AS "주문수량",
    status AS "체결상태",
    msg AS "메시지"
FROM orders
ORDER BY id DESC
LIMIT 50;


-- ------------------------------------------------------------------------------
-- 8. [봇 엔진 로그] 자동매매 봇 실행 로그 모니터링 (Bot Logs)
-- ------------------------------------------------------------------------------
SELECT 
    id,
    time AS "로그시간",
    type AS "로그구분",
    message AS "로그내용"
FROM bot_logs
ORDER BY id DESC
LIMIT 100;


-- ------------------------------------------------------------------------------
-- 9. [유지보수 / 관리용 쿼리] (필요 시 주석 해제 후 실행)
-- ------------------------------------------------------------------------------
-- 가상계좌 원금 1,000만원 리셋 및 보유 포지션 비우기
-- UPDATE account_state SET paper_capital = 10000000, initial_capital = 10000000 WHERE id = 1;
-- DELETE FROM positions;

-- 가상계좌 현금 잔고 수동 조정 (예: 2,000만원으로 설정 시)
-- UPDATE account_state SET paper_capital = 20000000 WHERE id = 1;

-- 모든 거래일지 및 로그 초기화
-- DELETE FROM closed_trades;
-- DELETE FROM orders;
-- DELETE FROM bot_logs;
