import os

os.makedirs('auto_trader/static', exist_ok=True)

html_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Trader Dashboard</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="dashboard-container">
        <header class="obsidian-panel">
            <h1>AI VibeTrading Dashboard</h1>
            <div class="status-indicator">
                <span id="bot-status" class="status-dot off"></span>
                <span id="bot-status-text">Bot Offline</span>
            </div>
        </header>

        <main>
            <div class="obsidian-panel card">
                <h2>계좌 자산</h2>
                <p class="balance" id="account-balance">0 원</p>
                <div class="controls">
                    <button class="obsidian-btn" onclick="startBot()">봇 시작</button>
                    <button class="obsidian-btn" onclick="stopBot()">봇 정지</button>
                </div>
            </div>
            
            <div class="obsidian-panel card">
                <h2>보유 종목</h2>
                <ul id="positions-list">
                    <li>보유 종목이 없습니다.</li>
                </ul>
            </div>
        </main>
    </div>

    <!-- 얇고 긴 티커 테이프 줄 (하단) -->
    <div class="ticker-wrap obsidian-panel">
        <div class="ticker-move" id="ticker-content">
            <!-- JS로 데이터 채워짐 -->
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>
'''

css_content = '''@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');

body {
    margin: 0;
    padding: 0;
    font-family: 'Noto Sans KR', sans-serif;
    color: #e0e0e0;
    /* 에메랄드 + 어두운 빛반사 배경 */
    background: radial-gradient(circle at 20% 30%, rgba(46, 204, 113, 0.15), transparent 60%),
                radial-gradient(circle at 80% 70%, rgba(26, 188, 156, 0.1), transparent 50%),
                linear-gradient(135deg, #0f171e, #1a252c);
    background-attachment: fixed;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.obsidian-panel {
    /* 흑요석 글래스모피즘 */
    background: rgba(15, 20, 25, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.15);
}

.dashboard-container {
    max-width: 1000px;
    margin: 40px auto;
    flex: 1;
    width: 90%;
}

header {
    padding: 20px 30px;
    border-radius: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

header h1 {
    margin: 0;
    font-size: 1.5rem;
    background: linear-gradient(90deg, #2ecc71, #1abc9c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(0,0,0,0.5);
}

.status-dot.on { background: #2ecc71; box-shadow: 0 0 10px #2ecc71; }
.status-dot.off { background: #e74c3c; box-shadow: 0 0 10px #e74c3c; }

main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.card {
    padding: 30px;
    border-radius: 16px;
}

.card h2 {
    margin-top: 0;
    font-size: 1.2rem;
    color: #a8b8c8;
}

.balance {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 20px 0;
    color: #fff;
    text-shadow: 0 0 15px rgba(46, 204, 113, 0.4);
}

.controls {
    display: flex;
    gap: 15px;
}

.obsidian-btn {
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    /* 흑요석 버튼 */
    background: linear-gradient(145deg, #2c3e50, #1a252f);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #e0e0e0;
    box-shadow: 3px 3px 6px rgba(0,0,0,0.4), inset 1px 1px 2px rgba(255,255,255,0.1);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.obsidian-btn:hover {
    background: linear-gradient(145deg, #34495e, #2c3e50);
    box-shadow: 0 0 15px rgba(46, 204, 113, 0.5), inset 1px 1px 3px rgba(255,255,255,0.3);
    transform: translateY(-2px);
    color: #fff;
}

/* 티커 테이프 (왼쪽에서 오른쪽으로 흐름) */
.ticker-wrap {
    width: 100%;
    height: 40px;
    overflow: hidden;
    position: fixed;
    bottom: 0;
    left: 0;
    display: flex;
    align-items: center;
    border-top: 1px solid rgba(255,255,255,0.05);
    border-radius: 0;
}

.ticker-move {
    display: flex;
    white-space: nowrap;
    /* 왼쪽에서 오른쪽 이동 애니메이션 */
    animation: tickerLeftToRight 30s linear infinite;
}

.ticker-item {
    padding: 0 30px;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.ticker-item .up { color: #e74c3c; } /* 한국은 빨강이 상승 */
.ticker-item .down { color: #3498db; } /* 파랑이 하락 */

@keyframes tickerLeftToRight {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100vw); }
}
'''

js_content = '''async function fetchDashboardData() {
    try {
        const balRes = await fetch('/api/v1/account/balance');
        const balData = await balRes.json();
        document.getElementById('account-balance').innerText = balData.balance.toLocaleString() + ' 원';

        const sysRes = await fetch('/');
        const sysData = await sysRes.json();
        const dot = document.getElementById('bot-status');
        const txt = document.getElementById('bot-status-text');
        
        if (sysData.bot_running) {
            dot.className = 'status-dot on';
            txt.innerText = 'Bot Running';
        } else {
            dot.className = 'status-dot off';
            txt.innerText = 'Bot Offline';
        }

    } catch (e) {
        console.error('Error fetching data:', e);
    }
}

async function fetchTickerTape() {
    try {
        const res = await fetch('/api/v1/market/ticker-tape');
        const data = await res.json();
        const container = document.getElementById('ticker-content');
        
        let html = '';
        data.tickers.forEach(item => {
            const colorClass = item.change > 0 ? 'up' : (item.change < 0 ? 'down' : '');
            const sign = item.change > 0 ? '+' : '';
            html += `<div class="ticker-item">
                <span>${item.name}(${item.symbol})</span>
                <strong>${item.price.toLocaleString()}</strong>
                <span class="${colorClass}">${sign}${item.change}%</span>
            </div>`;
        });
        
        container.innerHTML = html + html; // 반복을 위해 2배
    } catch (e) {
        console.error('Ticker fetch error:', e);
    }
}

async function startBot() {
    await fetch('/api/v1/bot/start', { method: 'POST' });
    fetchDashboardData();
}

async function stopBot() {
    await fetch('/api/v1/bot/stop', { method: 'POST' });
    fetchDashboardData();
}

fetchDashboardData();
fetchTickerTape();
setInterval(fetchDashboardData, 3000);
setInterval(fetchTickerTape, 10000);
'''

with open('auto_trader/static/index.html', 'w', encoding='utf-8') as f: f.write(html_content)
with open('auto_trader/static/style.css', 'w', encoding='utf-8') as f: f.write(css_content)
with open('auto_trader/static/script.js', 'w', encoding='utf-8') as f: f.write(js_content)

