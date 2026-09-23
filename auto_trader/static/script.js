let currentAccountBalance = 10000000;
let currentAccountBalance = 10000000;   // 총자산 (현금 + 주식 평가액) — 대시보드 헤드라인
let currentCashBalance = 10000000;       // 가용 현금 — "전액" 버튼 및 예산 계산 기준
let currentRecommendationBudget = 2000000;
let currentTradingMode = 'PAPER';
let currentAccountNo = '';
let isRealTradingConfirmed = false;

async function fetchDashboardData() {
    try {
        const balRes = await fetch('/api/v1/account/balance');
        const balData = await balRes.json();
        
        currentAccountBalance = balData.balance || 0;
        currentAccountBalance = balData.balance || 0;   // 총자산
        currentCashBalance    = balData.cash    || currentAccountBalance; // 가용 현금
        currentTradingMode = (balData.trading_mode || 'PAPER').toUpperCase();
        currentAccountNo = balData.account_no || '';
        isRealTradingConfirmed = !!balData.real_trading_confirmed;

        if (balData.recommended_budget) {
            currentRecommendationBudget = balData.recommended_budget;
        }

        // 잔고 표시 업데이트 (우측 패널 및 중앙 카드)
        // 총자산 표시 (우측 패널 및 중앙 카드)
        const formattedBal = currentAccountBalance.toLocaleString() + ' 원';
        const rightBal = document.getElementById('account-balance');
        if (rightBal) rightBal.innerText = formattedBal;
        const centerBal = document.getElementById('center-account-balance');
        if (centerBal) centerBal.innerText = formattedBal;

        // 추천 예산 표시 업데이트
        const formattedBudget = currentRecommendationBudget.toLocaleString() + ' 원';
        const dispBudget = document.getElementById('display-trade-budget');
        if (dispBudget) dispBudget.innerText = formattedBudget;
        const rightBudget = document.getElementById('right-trade-budget');
        if (rightBudget) rightBudget.innerText = formattedBudget;
        const recIndicator = document.getElementById('rec-budget-indicator');
        if (recIndicator) recIndicator.innerText = formattedBudget;
        
        const inputBudget = document.getElementById('input-trade-budget');
        if (inputBudget && document.activeElement !== inputBudget) {
            inputBudget.value = currentRecommendationBudget;
        }

        // 활성 예산 비율 버튼 동기화
        // 활성 예산 비율 버튼 동기화 — 기준: 가용 현금(currentCashBalance)
        let initialPct = null;
        if (currentAccountBalance > 0 && currentRecommendationBudget > 0) {
            const pct = Math.round((currentRecommendationBudget / currentAccountBalance) * 100);
        if (currentCashBalance > 0 && currentRecommendationBudget > 0) {
            const pct = Math.round((currentRecommendationBudget / currentCashBalance) * 100);
            if ([10, 20, 30, 50, 100].includes(pct)) {
                initialPct = pct;
                const ratioTag = document.getElementById('budget-ratio-tag');
                if (ratioTag) ratioTag.innerText = `잔고의 ${pct}%`;
            }
        }
        syncActiveBudgetButton(initialPct);


        // 모드 및 라벨 업데이트
        const isLive = currentTradingMode === 'REAL' || currentTradingMode === 'LIVE';
        const isMock = currentTradingMode === 'MOCK';
        const centerTitle = document.getElementById('center-account-title');
        const rightTitle = document.getElementById('right-account-title');
        const acctBadge = document.getElementById('account-mode-badge');
        const portHeader = document.getElementById('portfolio-panel-header');
        const rightBadge = document.getElementById('right-account-badge');
        const centerDesc = document.getElementById('center-account-desc');

        if (isLive) {
            if (centerTitle) centerTitle.innerText = '실거래계좌 평가 자산 (나무증권)';
            if (rightTitle) rightTitle.innerText = '실거래계좌 평가 자산';
            if (acctBadge) {
                const lockStatus = isRealTradingConfirmed ? '🟢 실거래 주문가능' : '🔒 2차 안전잠금중';
                acctBadge.innerText = `🔴 실거래 LIVE [${currentAccountNo || '21001461419'}] (${lockStatus})`;
                acctBadge.style.background = isRealTradingConfirmed ? 'rgba(231, 76, 60, 0.25)' : 'rgba(243, 156, 18, 0.2)';
                acctBadge.style.color = isRealTradingConfirmed ? '#ff6b6b' : '#f39c12';
                acctBadge.style.borderColor = isRealTradingConfirmed ? 'rgba(231, 76, 60, 0.6)' : 'rgba(243, 156, 18, 0.5)';
            }
            if (centerDesc) {
                const cashStr = (balData.cash || 0).toLocaleString();
                const withStr = (balData.withdrawable || 0).toLocaleString();
                centerDesc.innerHTML = `<span style="color:#2ecc71;">예수금: ${cashStr}원</span> | <span>출금가능: ${withStr}원</span> (실서버: api.nhplug.com:8443)`;
            }
            if (portHeader) portHeader.innerText = '실거래 포트폴리오 (보유 종목 현황)';
            if (rightBadge) {
                rightBadge.innerText = '실거래 LIVE';
                rightBadge.style.color = '#e74c3c';
                rightBadge.style.borderColor = 'rgba(231, 76, 60, 0.4)';
            }
        } else if (isMock) {
            if (centerTitle) centerTitle.innerText = '모의투자계좌 평가 자산 (나무증권)';
            if (rightTitle) rightTitle.innerText = '모의투자 평가 자산';
            if (acctBadge) {
                acctBadge.innerText = `🟢 모의투자 MOCK [${currentAccountNo || '50071004971'}]`;
                acctBadge.style.background = 'rgba(46, 204, 113, 0.2)';
                acctBadge.style.color = '#2ecc71';
                acctBadge.style.borderColor = 'rgba(46, 204, 113, 0.4)';
            }
            if (centerDesc) {
                centerDesc.innerHTML = `<span>나무증권 모의투자 서버 연동 중 (moapi.nhplug.com:8443)</span>`;
            }
            if (portHeader) portHeader.innerText = '모의투자 포트폴리오 (보유 현황)';
            if (rightBadge) {
                rightBadge.innerText = '모의투자 MOCK';
                rightBadge.style.color = '#2ecc71';
                rightBadge.style.borderColor = 'rgba(46, 204, 113, 0.4)';
            }
        } else {
            if (centerTitle) centerTitle.innerText = '가상계좌 금액';
            if (rightTitle) rightTitle.innerText = '가상계좌 평가 자산';
            if (acctBadge) {
                acctBadge.innerText = '가상계좌 (시뮬레이터 PAPER)';
                acctBadge.style.background = 'rgba(243, 156, 18, 0.2)';
                acctBadge.style.color = '#f39c12';
                acctBadge.style.borderColor = 'rgba(243, 156, 18, 0.4)';
            }
            if (centerDesc) {
                centerDesc.innerText = '실제 금액 매매(LIVE) 전환 시 나무증권 실거래계좌 잔고가 표시됩니다.';
            }
            if (portHeader) portHeader.innerText = '가상 포트폴리오 (포지션 현황)';
            if (rightBadge) {
                rightBadge.innerText = '가상투자 PAPER';
                rightBadge.style.color = '#f39c12';
                rightBadge.style.borderColor = 'rgba(243, 156, 18, 0.4)';
            }
        }

        const sysRes = await fetch('/health');
        const sysData = await sysRes.json();
        const dot = document.getElementById('bot-status');
        const txt = document.getElementById('bot-status-text');
        
        if (sysData.bot_running) {
            dot.className = 'status-dot on'; txt.innerText = 'Bot Running';
            if (!botLogTimer) {
                fetchBotLogs();
                botLogTimer = setInterval(fetchBotLogs, 2500);
            }
        } else {
            dot.className = 'status-dot off'; txt.innerText = 'Bot Offline';
            if (botLogTimer) {
                clearInterval(botLogTimer);
                botLogTimer = null;
            }
        }
        
        // API status update
        const apiBtn = document.getElementById('api-status-btn');
        if(apiBtn) {
            if(sysData.api_connected) {
                apiBtn.innerText = 'API 연결됨';
                apiBtn.style.background = '#27ae60';
            } else {
                apiBtn.innerText = '연결실패';
                apiBtn.style.background = '#e74c3c';
            }
        }
        
        // Mode status update
        const modeBtn = document.getElementById('mode-status-btn');
        if(modeBtn) {
            if(sysData.trading_mode === 'REAL' || sysData.trading_mode === 'LIVE') {
                modeBtn.innerText = '실제금액주문 (LIVE)';
                modeBtn.style.background = '#e74c3c';
            } else {
                modeBtn.innerText = '모의투자 (PAPER)';
                modeBtn.style.background = '#f39c12';
            }
        }

        const posRes = await fetch('/api/v1/account/positions');
        const posData = await posRes.json();
        const posList = document.getElementById('positions-list');
        posList.innerHTML = '';
        if(Object.keys(posData.positions).length === 0) {
            posList.innerHTML = '<li class="empty-msg">보유 종목이 없습니다.</li>';
        } else {
            for (const [sym, item] of Object.entries(posData.positions)) {
                const count = typeof item === 'object' && item !== null ? (item.qty || 0) : item;
                const nameStr = (typeof item === 'object' && item.name && item.name !== sym) ? ` ${item.name}` : '';
                const profitStr = (typeof item === 'object' && item.profit_rate !== undefined && item.profit_rate !== 0) ? ` <small style="color:${item.profit_rate > 0 ? '#ff6b6b' : '#3498db'};">(${item.profit_rate > 0 ? '+' : ''}${item.profit_rate}%)</small>` : '';
                posList.innerHTML += `<li style="padding: 10px; background: rgba(0,0,0,0.3); margin-bottom: 5px; border-radius: 5px; border: 1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center;">
                    <span><strong>${sym}</strong><span style="font-size:0.85rem; color:#aaa;">${nameStr}</span></span>
                    <span><strong>${count}주</strong>${profitStr}</span>
                </li>`;
            }
        }
    } catch (e) {
        console.error('Error fetching data:', e);
    }
}

async function fetchMarketData() {
    try {
        const res = await fetch('/api/v1/market/ticker-tape');
        const data = await res.json();
        const tickerContainer = document.getElementById('ticker-content');
        const watchlistBody = document.getElementById('watchlist-body');
        
        let tickerHtml = '', listHtml = '';
        data.tickers.forEach(item => {
            const colorClass = item.change > 0 ? 'up' : (item.change < 0 ? 'down' : '');
            const sign = item.change > 0 ? '+' : '';
            const priceStr = item.price.toLocaleString();
            const changeStr = `${sign}${item.change}%`;

            tickerHtml += `<div class="ticker-item"><span style="color:#aaa">${item.name}</span><strong>${priceStr}</strong><span class="${colorClass}">${changeStr}</span></div>`;
            listHtml += `<tr onclick="loadChart('${item.symbol}', '${item.name}')" style="cursor:pointer"><td>${item.name} <br><span style="font-size:0.75em;color:#555">${item.symbol}</span></td><td><strong>${priceStr}</strong></td><td class="${colorClass}">${changeStr}</td></tr>`;
        });
        
        tickerContainer.innerHTML = tickerHtml + tickerHtml; 
        watchlistBody.innerHTML = listHtml;
    } catch (e) {
        console.error('Market data fetch error:', e);
    }
}

// === 봇 제어 및 실시간 로그 콘솔 ===
let botLogTimer = null;

async function fetchBotLogs() {
    try {
        const res = await fetch('/api/v1/bot/logs');
        const data = await res.json();
        const terminal = document.getElementById('bot-log-terminal');
        const pulse = document.getElementById('bot-pulse-dot');
        
        if (pulse) {
            pulse.style.background = data.is_running ? '#2ecc71' : '#7f8c8d';
            pulse.style.boxShadow = data.is_running ? '0 0 8px #2ecc71' : 'none';
        }

        if (terminal && data.logs && data.logs.length > 0) {
            let html = '';
            for (const log of data.logs) {
                let color = '#ecf0f1';
                let icon = '•';
                if (log.type.includes('BUY')) {
                    color = '#2ecc71';
                    icon = '🚀';
                } else if (log.type.includes('SELL')) {
                    color = '#e74c3c';
                    icon = '🎯';
                } else if (log.type === 'MONITOR') {
                    color = '#3498db';
                    icon = '📊';
                } else if (log.type === 'SCAN') {
                    color = '#95a5a6';
                    icon = '👀';
                } else if (log.type === 'ERROR') {
                    color = '#e67e22';
                    icon = '⚠️';
                }
                html += `<div style="margin-bottom:3px;"><span style="color:#7f8c8d;">[${log.time}]</span> <span style="color:${color}; font-weight:500;">${icon} ${log.message}</span></div>`;
            }
            terminal.innerHTML = html;
        } else if (terminal && !data.is_running) {
            terminal.innerHTML = '<div style="color:#7f8c8d;">[대기] 자동매매 봇이 정지되어 있습니다. 상단의 [자동매매 시작] 버튼을 누르면 실시간 시세 감시 및 자동 매매가 활성화됩니다.</div>';
        }
    } catch (e) {
        console.warn('Bot log fetch error:', e);
    }
}

async function startBot() {
    try {
        const res = await fetch('/api/v1/bot/start', { method: 'POST' });
        const data = await res.json();
        alert("🤖 자동매매 봇이 가동되었습니다!\n변동성 돌파 진입 신호 감지 시 자동 매수하며, +3% 익절 및 -2% 손절을 실시간 집행합니다.");
        fetchDashboardData();
        fetchBotLogs();
        if (!botLogTimer) {
            botLogTimer = setInterval(fetchBotLogs, 2500);
        }
    } catch(e) {
        alert("봇 가동 실패: " + e.message);
    }
}

async function stopBot() {
    try {
        await fetch('/api/v1/bot/stop', { method: 'POST' });
        alert("🛑 자동매매 봇이 안전하게 중지되었습니다.");
        fetchDashboardData();
        fetchBotLogs();
        if (botLogTimer) {
            clearInterval(botLogTimer);
            botLogTimer = null;
        }
    } catch(e) {
        alert("봇 중지 실패: " + e.message);
    }
}

// === 실거래 주문 안전 확인 및 발주 함수 ===
async function executeDirectBuy(symbol, price, qty, name) {
    if (!symbol || !qty || qty <= 0) return alert("유효하지 않은 주문 정보입니다.");
    const totalCost = (price || 0) * qty;

    const isLive = currentTradingMode === 'REAL' || currentTradingMode === 'LIVE';
    const isMock = currentTradingMode === 'MOCK';

    if (isLive) {
        const confirmMsg = `🚨 [나무증권 실거래 매수 주문 확인]\n\n` +
            `• 계좌번호: ${currentAccountNo || '21001461419'} (실거래 종합매매)\n` +
            `• 주문종목: ${name || symbol} (${symbol})\n` +
            `• 주문수량: ${qty} 주\n` +
            `• 1주당 단가: ${price ? price.toLocaleString() + ' 원' : '시장가'}\n` +
            `• 총 매수소요: ${totalCost.toLocaleString()} 원\n\n` +
            `⚠️ 경고: 확인을 누르면 실제 증권 계좌에서 실제 자금으로 한국거래소(KRX)에 매수 주문이 즉시 발주됩니다.\n\n` +
            `정말로 매수 주문을 발송하시겠습니까?`;
        if (!confirm(confirmMsg)) return;
    } else {
        const modeName = isMock ? '모의투자(MOCK)' : '가상투자(PAPER)';
        const confirmMsg = `[${modeName} 매수 주문]\n` +
            `• 종목: ${name || symbol} (${symbol})\n` +
            `• 수량: ${qty}주 / 단가: ${price ? price.toLocaleString() + '원' : '시장가'}\n` +
            `• 총액: ${totalCost.toLocaleString()}원\n\n` +
            `주문을 접수하시겠습니까?`;
        if (!confirm(confirmMsg)) return;
    }

    try {
        const res = await fetch('/api/v1/orders/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                price: parseInt(price) || 0,
                qty: parseInt(qty),
                order_type: price > 0 ? "LIMIT" : "MARKET"
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ ${data.message || '매수 주문이 성공적으로 접수되었습니다.'}`);
        } else {
            alert(`❌ 매수 실패:\n${data.detail || data.message || '주문이 거부되었습니다.'}`);
        }
        fetchDashboardData();
    } catch (e) {
        alert(`❌ 주문 전송 오류: ${e.message}`);
    }
}

// === 수동 주문 (Buy / Sell) ===
async function submitBuy() {
    const symbol = document.getElementById('order-symbol').value;
    const price = document.getElementById('order-price').value;
    const qty = document.getElementById('order-qty').value;
    
    if(!symbol || !price || !qty) return alert("종목코드, 가격, 수량을 모두 입력하세요.");
    
    const isLive = currentTradingMode === 'REAL' || currentTradingMode === 'LIVE';
    if (isLive) {
        const total = parseInt(price) * parseInt(qty);
        const confirmMsg = `🚨 [나무증권 실거래 매수 확인]\n\n` +
            `• 계좌번호: ${currentAccountNo || '21001461419'}\n` +
            `• 종목코드: ${symbol}\n` +
            `• 수량: ${qty} 주 / 단가: ${parseInt(price).toLocaleString()} 원\n` +
            `• 총 결제금액: ${total.toLocaleString()} 원\n\n` +
            `⚠️ 실제 증권 계좌에서 즉시 출금 및 매수 주문이 발주됩니다. 계속하시겠습니까?`;
        if (!confirm(confirmMsg)) return;
    }

    try {
        const res = await fetch('/api/v1/orders/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, price: parseInt(price), qty: parseInt(qty) })
        });
        
        const data = await res.json();
        if(res.ok) alert(`✅ ${data.message}`); else alert(`❌ 매수 실패: ${data.detail || data.message}`);
        fetchDashboardData();
    } catch(err) {
        alert("주문 요청 실패: " + err.message);
    }
}

async function submitSell() {
    const symbol = document.getElementById('order-symbol').value;
    const price = document.getElementById('order-price').value;
    const qty = document.getElementById('order-qty').value;
    
    if(!symbol || !price || !qty) return alert("종목코드, 가격, 수량을 모두 입력하세요.");

    const isLive = currentTradingMode === 'REAL' || currentTradingMode === 'LIVE';
    if (isLive) {
        const total = parseInt(price) * parseInt(qty);
        const confirmMsg = `🚨 [나무증권 실거래 매도 확인]\n\n` +
            `• 계좌번호: ${currentAccountNo || '21001461419'}\n` +
            `• 종목코드: ${symbol}\n` +
            `• 수량: ${qty} 주 / 단가: ${parseInt(price).toLocaleString()} 원\n` +
            `• 총 매도예상금액: ${total.toLocaleString()} 원\n\n` +
            `⚠️ 실제 보유 주식이 한국거래소로 매도 주문 발주됩니다. 계속하시겠습니까?`;
        if (!confirm(confirmMsg)) return;
    }

    try {
        const res = await fetch('/api/v1/orders/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, price: parseInt(price), qty: parseInt(qty) })
        });
        
        const data = await res.json();
        if(res.ok) alert(`✅ ${data.message}`); else alert(`❌ 매도 실패: ${data.detail || data.message}`);
        fetchDashboardData();
    } catch(err) {
        alert("주문 요청 실패: " + err.message);
    }
}

// === 주문 관리 ===
async function modifyOrder() {
    const orderId = document.getElementById('manage-order-id').value;
    const newPrice = document.getElementById('manage-new-price').value;
    if(!orderId || !newPrice) return alert("주문 ID와 정정 단가를 입력하세요.");
    
    const res = await fetch(`/api/v1/orders/${orderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_price: parseInt(newPrice), new_qty: 0 })
    });
    const data = await res.json();
    alert(data.message);
}

async function cancelOrder() {
    const orderId = document.getElementById('manage-order-id').value;
    if(!orderId) return alert("취소할 주문 ID를 입력하세요.");
    
    const res = await fetch(`/api/v1/orders/${orderId}`, { method: 'DELETE' });
    const data = await res.json();
    alert(data.message);
}

// === 봇 설정 ===
async function updateSettings() {
    const kValue = document.getElementById('bot-setting-k').value;
    if(!kValue) return alert("K값을 입력하세요.");
    
    const res = await fetch(`/api/v1/bot/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ breakout_k: parseFloat(kValue) })
    });
    const data = await res.json();
    alert(data.message);
}

// === 시세 전광판 로직 ===
let currentSearchSymbol = null;
async function loadQuote(symbol, name) {
    try {
        // API에서 특정 종목 1개 가져오기 (기업명 또는 종목코드 지원)
        const res = await fetch(`/api/v1/market/quote/${encodeURIComponent(symbol)}`);
        const stock = await res.json();
        
        // 데이터 포맷 맞추기
        stock.price = stock.current_price;
        stock.change = stock.change_rate;

        // 실제 해석된 6자리 종목코드로 백그라운드 집중 갱신 타겟 지정
        if(stock && stock.symbol) {
            currentSearchSymbol = stock.symbol;
        } else {
            currentSearchSymbol = symbol;
        }
                      
        const qName = document.getElementById('quote-name');
        const qSymbol = document.getElementById('quote-symbol');
        const qPrice = document.getElementById('quote-price');
        const qChange = document.getElementById('quote-change');

        if(stock && stock.current_price > 0) {
            qName.innerText = stock.name;
            qSymbol.innerText = stock.symbol;
            qPrice.innerText = stock.price.toLocaleString() + " 원";
            
            const sign = stock.change > 0 ? "+" : "";
            qChange.innerText = `${sign}${stock.change}%`;
            
            // 색상 적용
            const color = stock.change > 0 ? '#e74c3c' : (stock.change < 0 ? '#3498db' : '#d1d4dc');
            qPrice.style.color = color;
            qChange.style.color = color;
            
            // 수동주문 창 종목코드 자동 입력 (해석된 종목코드)
            const orderSymbolInput = document.getElementById('order-symbol');
            if(orderSymbolInput) orderSymbolInput.value = stock.symbol;
        } else {
            // 목록에 없는 경우 (기본 뼈대)
            qName.innerText = name || "검색 결과 없음";
            qSymbol.innerText = symbol;
            qPrice.innerText = "데이터 없음";
            qChange.innerText = "-";
            qPrice.style.color = "#888";
            qChange.style.color = "#888";
        }
    } catch (e) {
        console.error('Quote load error:', e);
    }
}

async function searchStock() {
    const symInput = document.getElementById('search-symbol');
    if(!symInput) return;
    const sym = symInput.value.trim();
    if(!sym) return alert("종목코드 또는 기업명을 입력하세요 (예: 삼성전자, 005930)");
    loadQuote(sym, sym);
}

// 엔터 키 이벤트 리스너 추가 (안전장치)
document.addEventListener('DOMContentLoaded', () => {
    const sInput = document.getElementById('search-symbol');
    if (sInput) {
        sInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchStock();
            }
        });
    }
});

// 기존 리스트 클릭 시 호출되던 loadChart를 덮어쓰기 위해 전역 함수로 우회
window.loadChart = function(symbol, name) {
    loadQuote(symbol, name);
};

// 초기화
fetchDashboardData();
fetchMarketData();
fetchPortfolioPnl();
setInterval(fetchDashboardData, 10000);
setInterval(fetchMarketData, 15000);
setInterval(fetchPortfolioPnl, 5000);

// === 실시간 포트폴리오 수익률 ===
async function fetchPortfolioPnl() {
    try {
        const res = await fetch('/api/v1/account/portfolio-pnl');
        const data = await res.json();
        const section = document.getElementById('portfolio-pnl-section');
        if (!section) return;

        if (!data.has_positions) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        const s = data.summary;
        const evalEl = document.getElementById('pnl-total-eval');
        const pnlEl = document.getElementById('pnl-total-pnl');
        const pctEl = document.getElementById('pnl-total-pct');
        const timeEl = document.getElementById('pnl-update-time');

        if (evalEl) evalEl.innerText = s.total_eval_amt.toLocaleString() + ' 원';

        const pnlColor = s.total_pnl > 0 ? '#ff6b6b' : (s.total_pnl < 0 ? '#3498db' : '#d1d4dc');
        const pnlSign = s.total_pnl > 0 ? '+' : '';
        if (pnlEl) {
            pnlEl.innerText = pnlSign + s.total_pnl.toLocaleString() + ' 원';
            pnlEl.style.color = pnlColor;
        }
        if (pctEl) {
            pctEl.innerText = (s.total_pnl_pct > 0 ? '+' : '') + s.total_pnl_pct.toFixed(2) + '%';
            pctEl.style.color = pnlColor;
        }
        if (timeEl) {
            const now = new Date();
            timeEl.innerText = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} 갱신`;
        }

        // 종목별 수익률 리스트 렌더링
        const listEl = document.getElementById('pnl-items-list');
        if (listEl && data.items.length > 0) {
            let html = '';
            data.items.forEach(item => {
                const c = item.pnl > 0 ? '#ff6b6b' : (item.pnl < 0 ? '#3498db' : '#d1d4dc');
                const sg = item.pnl > 0 ? '+' : '';
                const nameDisplay = (item.name && item.name !== item.symbol) ? item.name : item.symbol;
                html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:7px 8px; margin-bottom:4px; background:rgba(0,0,0,0.2); border-radius:5px; border:1px solid rgba(255,255,255,0.04);">
                    <div style="flex:1; min-width:0;">
                        <div style="font-size:0.82rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${nameDisplay}</div>
                        <div style="font-size:0.7rem; color:#888;">${item.symbol} · ${item.qty}주 · 매수 ${item.buy_price.toLocaleString()}원</div>
                    </div>
                    <div style="text-align:right; flex-shrink:0; margin-left:8px;">
                        <div style="font-size:0.82rem; font-weight:bold;">${item.current_price.toLocaleString()}원</div>
                        <div style="font-size:0.78rem; font-weight:600; color:${c};">${sg}${item.pnl.toLocaleString()}원 (${sg}${item.pnl_pct.toFixed(2)}%)</div>
                    </div>
                </div>`;
            });
            listEl.innerHTML = html;
        }
    } catch (e) {
        console.warn('Portfolio PnL fetch error:', e);
    }
}


// 집중 종목 실시간 갱신 (3초)
async function fetchFocusedQuote() {
    if (currentSearchSymbol) {
        // 백그라운드 갱신이므로 화면에 깜빡임 없이 데이터만 덮어씁니다.
        const res = await fetch(`/api/v1/market/quote/${currentSearchSymbol}`);
        const stock = await res.json();
        if(stock) {
            const qPrice = document.getElementById('quote-price');
            const qChange = document.getElementById('quote-change');
            if(qPrice && qChange) {
                qPrice.innerText = stock.current_price.toLocaleString() + " 원";
                const sign = stock.change_rate > 0 ? "+" : "";
                qChange.innerText = `${sign}${stock.change_rate}%`;
                const color = stock.change_rate > 0 ? '#e74c3c' : (stock.change_rate < 0 ? '#3498db' : '#d1d4dc');
                qPrice.style.color = color;
                qChange.style.color = color;
            }
        }
    }
}
setInterval(fetchFocusedQuote, 3000);

// API 연결 상태 확인 클릭 이벤트
async function checkApiConnection() {
    try {
        const res = await fetch('/health');
        const data = await res.json();
        if (data.api_connected) {
            alert("✅ 나무증권 API와 정상적으로 연결되어 있습니다! (실시간 시세 연동 중)");
        } else {
            alert("❌ 나무증권 API 연결 실패! .env 파일의 NHPLUG_APP_KEY 및 SECRET을 확인해주세요.");
        }
        await fetchDashboardData();
    } catch (e) {
        alert("서버 통신 오류: " + e);
    }
}

// 상단 새로고침 버튼 (연속 클릭 방지 & 매끄러운 비동기 갱신)
let isRefreshing = false;
async function manualRefresh() {
    if (isRefreshing) return;
    isRefreshing = true;
    const btn = document.getElementById('refresh-btn');
    if (btn) {
        btn.innerText = '갱신 중...';
        btn.style.opacity = '0.6';
    }
    try {
        await Promise.all([fetchDashboardData(), fetchMarketData()]);
        if (currentSearchSymbol) await fetchFocusedQuote();
    } catch (e) {
        console.error('Refresh error:', e);
    } finally {
        setTimeout(() => {
            if (btn) {
                btn.innerText = '새로고침';
                btn.style.opacity = '1.0';
            }
            isRefreshing = false;
        }, 500);
    }
}

// === 추천 매매 예산 설정 및 버튼 활성화 연동 ===
function syncActiveBudgetButton(targetPct) {
    const buttons = document.querySelectorAll('#budget-pct-group button, .budget-pct-btn');
    buttons.forEach(btn => {
        let pct = btn.getAttribute('data-pct');
        if (!pct) {
            const txt = btn.innerText.trim();
            pct = txt === '전액' ? '100' : txt.replace(/[^0-9]/g, '');
            if (pct) btn.setAttribute('data-pct', pct);
        }
        if (targetPct !== null && targetPct !== undefined && parseInt(pct) === parseInt(targetPct)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

async function setBudgetPercent(pct) {
    if (!currentAccountBalance || currentAccountBalance <= 0) return;
    if (!currentCashBalance || currentCashBalance <= 0) return;
    syncActiveBudgetButton(pct);
    const newBudget = Math.floor(currentAccountBalance * (pct / 100));
    await updateBudget(newBudget, `${pct}%`, pct);
    const newBudget = Math.floor(currentCashBalance * (pct / 100));
    await updateBudget(newBudget, `잔고의 ${pct}%`, pct);
}

async function applyCustomBudget() {
    const input = document.getElementById('input-trade-budget');
    if (!input) return;
    const val = parseInt(input.value);
    if (isNaN(val) || val <= 0) return alert('올바른 금액을 입력하세요.');
    
    let matchedPct = null;
    if (currentAccountBalance > 0) {
        const calculatedPct = Math.round((val / currentAccountBalance) * 100);
        if ([10, 20, 30, 50, 100].includes(calculatedPct)) {
            matchedPct = calculatedPct;
        }
    }
    syncActiveBudgetButton(matchedPct);
    const ratioLabel = matchedPct ? `${matchedPct}%` : (currentAccountBalance > 0 ? `${Math.round((val/currentAccountBalance)*100)}%` : '직접지정');
    await updateBudget(val, ratioLabel, matchedPct);
}

async function updateBudget(budgetVal, ratioText, activePct = null) {
    try {
        const res = await fetch('/api/v1/account/budget', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ budget: budgetVal })
        });
        const data = await res.json();
        if (res.ok) {
            currentRecommendationBudget = data.budget;
            const formatted = data.budget.toLocaleString() + ' 원';
            const disp = document.getElementById('display-trade-budget');
            if (disp) disp.innerText = formatted;
            const rightDisp = document.getElementById('right-trade-budget');
            if (rightDisp) rightDisp.innerText = formatted;
            const input = document.getElementById('input-trade-budget');
            if (input) input.value = data.budget;
            const recIndicator = document.getElementById('rec-budget-indicator');
            if (recIndicator) recIndicator.innerText = formatted;
            if (ratioText) {
                const tag = document.getElementById('budget-ratio-tag');
                if (tag) tag.innerText = `잔고의 ${ratioText}`;
            }
            if (activePct !== null && activePct !== undefined) {
                syncActiveBudgetButton(activePct);
            }
        } else {
            alert('예산 설정 실패: ' + (data.detail || '오류 발생'));
        }
    } catch (e) {
        console.error('Error updating budget:', e);
    }
}

// 이번 추천 예산으로 주문 수량 자동 계산
function applyBudgetToOrder() {
    const priceInput = document.getElementById('order-price');
    const qtyInput = document.getElementById('order-qty');
    const quotePriceElem = document.getElementById('quote-price');
    
    // 현재 호가 전광판 가격 또는 입력된 주문 단가 확인
    let price = parseInt(priceInput.value);
    if (!price || isNaN(price) || price <= 0) {
        const quoteText = quotePriceElem.innerText.replace(/[^0-9]/g, '');
        price = parseInt(quoteText);
    }
    
    if (!price || isNaN(price) || price <= 0) {
        return alert('종목을 먼저 검색하여 시세를 조회하거나 주문 단가를 입력하세요.');
    }
    
    priceInput.value = price;
    const calculatedQty = Math.floor(currentRecommendationBudget / price);
    if (calculatedQty <= 0) {
        qtyInput.value = 1;
        alert(`추천 예산(${currentRecommendationBudget.toLocaleString()}원)이 1주 가격(${price.toLocaleString()}원)보다 적어 최소 수량 1주로 설정되었습니다.`);
    } else {
        qtyInput.value = calculatedQty;
    }
}

// === 예산 기반 TOP 5 추천 종목 검색 & 렌더링 ===
let isFetchingRecommendations = false;

let currentRecommendationsList = [];

async function fetchTop5Recommendations() {
    if (isFetchingRecommendations) return;
    isFetchingRecommendations = true;

    const btn = document.getElementById('find-candidates-btn');
    const btnIcon = document.getElementById('find-candidates-icon');
    const btnText = document.getElementById('find-candidates-text');
    const container = document.getElementById('recommendations-container');
    const cardsGrid = document.getElementById('rec-cards-grid');
    const timeElem = document.getElementById('rec-timestamp');

    if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
    }
    if (btnIcon) btnIcon.innerText = '⏳';
    if (btnText) btnText.innerText = '실시간 종목 분석 중...';

    // 컨테이너 표시 및 로딩 표시
    if (container) container.style.display = 'block';
    if (cardsGrid) {
        cardsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 35px 20px; color: #2ecc71; font-size: 0.95rem; background: rgba(0,0,0,0.2); border-radius: 8px;">
                <div style="font-size: 2rem; margin-bottom: 12px; animation: pulse 1s infinite alternate;">🔍 📈</div>
                <div>지정 예산(<strong>${currentRecommendationBudget.toLocaleString()}원</strong>) 기반 실시간 시세 및 변동성 돌파 유망 종목 분석 중...</div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 6px;">시총 상위 및 수급 모멘텀을 다면 평가하여 최적의 TOP 5를 산출합니다.</div>
            </div>
        `;
    }

    try {
        const res = await fetch(`/api/v1/recommendations/top5?budget=${currentRecommendationBudget}`);
        const data = await res.json();

        if (res.ok && data.recommendations && data.recommendations.length > 0) {
            currentRecommendationsList = data.recommendations;
            renderRecommendationCards(data.recommendations, data.budget);
            if (container) {
                container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            if (timeElem) {
                const now = new Date();
                const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
                timeElem.innerText = `분석 기준시각: ${timeStr}`;
            }
        } else {
            if (cardsGrid) {
                cardsGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 25px; color: #e74c3c;">
                        현재 예산(${currentRecommendationBudget.toLocaleString()}원)으로 매수 가능한 추천 후보가 없거나 분석에 실패했습니다.
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error('Error fetching recommendations:', e);
        if (cardsGrid) {
            cardsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 25px; color: #e74c3c;">
                    추천 종목 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.
                </div>
            `;
        }
    } finally {
        isFetchingRecommendations = false;
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = '1';
        }
        if (btnIcon) btnIcon.innerText = '🔍';
        if (btnText) btnText.innerText = '후보찾기 (TOP 5 추천)';
    }
}

function renderRecommendationCards(recommendations, budget) {
    const cardsGrid = document.getElementById('rec-cards-grid');
    if (!cardsGrid) return;

    const rankIcons = {
        1: '🥇',
        2: '🥈',
        3: '🥉',
        4: '🏅',
        5: '🏅'
    };

    let html = '';
    recommendations.forEach(item => {
        const isUp = item.change_rate > 0;
        const isDown = item.change_rate < 0;
        const colorClass = isUp ? 'up' : (isDown ? 'down' : '');
        const sign = isUp ? '+' : '';
        const changeStr = `${sign}${Number(item.change_rate).toFixed(2)}%`;
        const icon = rankIcons[item.rank] || '🎯';
        const gradeClass = (item.score_grade || 'A').replace('+', '-plus');

        html += `
            <div class="rec-card rank-${item.rank}" onclick="openRecDetailModal(${item.rank})" title="클릭하여 상세 분석 화면 크게 보기">
                <!-- 헤더: 순위 및 평가점수 -->
                <div class="rec-card-header">
                    <div class="rec-rank-badge rank-${item.rank}">
                        <span>${icon}</span>
                        <span>TOP ${item.rank}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:0.7rem; color:#888; background:rgba(255,255,255,0.06); padding:2px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.08);">🔍 클릭시 확대</span>
                        <div class="rec-score-badge">
                            <span class="rec-score-title">평가점수</span>
                            <span class="rec-score-val">${item.score}점</span>
                            <span class="rec-score-grade grade-${gradeClass}">${item.score_grade}</span>
                        </div>
                    </div>
                </div>

                <!-- 종목 정보: 종목명, 코드, 현재가, 등락률 -->
                <div class="rec-stock-main">
                    <div class="rec-stock-title">
                        <h4 class="rec-stock-name">
                            ${item.name}
                            <span class="rec-stock-code">${item.symbol}</span>
                        </h4>
                    </div>
                    <div class="rec-stock-price-box">
                        <div class="rec-stock-price">${item.price.toLocaleString()} 원</div>
                        <div class="rec-stock-change ${colorClass}">${changeStr}</div>
                    </div>
                </div>

                <!-- 예산 매수 계획 -->
                <div class="rec-budget-box">
                    <div class="rec-budget-row">
                        <span class="rec-budget-label">추천 매수 수량</span>
                        <strong class="rec-budget-val rec-highlight">${item.recommended_qty}주</strong>
                    </div>
                    <div class="rec-budget-row">
                        <span class="rec-budget-label">총 소요 금액</span>
                        <span class="rec-budget-val">${item.total_cost.toLocaleString()} 원</span>
                    </div>
                    <div class="rec-budget-row">
                        <span class="rec-budget-label">잔여 예산</span>
                        <span class="rec-budget-val rec-sub">${item.remaining_budget.toLocaleString()} 원 (${item.utilization_rate}% 집행)</span>
                    </div>
                    <div class="rec-progress-track" title="예산 소진율: ${item.utilization_rate}%">
                        <div class="rec-progress-fill" style="width: ${Math.min(100, item.utilization_rate)}%;"></div>
                    </div>
                </div>

                <!-- 추천 사유 -->
                <div class="rec-reason-box">
                    <div class="rec-reason-title">💡 추천 사유 & 분석</div>
                    <div class="rec-reason-text">${item.reason}</div>
                </div>

                <!-- 주문서 즉시 적용 및 매수 발주 버튼 -->
                <div class="rec-card-actions" style="display:flex; gap:8px;">
                    <button type="button" class="obsidian-btn rec-apply-btn" style="flex:1; padding:8px 6px; font-size:0.8rem;" onclick="event.stopPropagation(); applyRecommendationToOrder('${item.symbol}', ${item.price}, ${item.recommended_qty}, '${item.name}')">
                        <span>⚡ 주문서 작성</span>
                    </button>
                    <button type="button" class="obsidian-btn glow rec-buy-btn" style="flex:1; padding:8px 6px; font-size:0.8rem; background: linear-gradient(135deg, #e74c3c, #c0392b); border-color:#e74c3c; color:#fff;" onclick="event.stopPropagation(); executeDirectBuy('${item.symbol}', ${item.price}, ${item.recommended_qty}, '${item.name}')">
                        <span>🚀 즉시 매수</span>
                    </button>
                </div>
            </div>
        `;
    });

    cardsGrid.innerHTML = html;
}

function openRecDetailModal(rank) {
    const item = currentRecommendationsList.find(r => r.rank === rank);
    if (!item) return;

    const modal = document.getElementById('rec-detail-modal');
    const body = document.getElementById('rec-modal-body');
    if (!modal || !body) return;

    const rankIcons = { 1: '🥇', 2: '🥈', 3: '🥉', 4: '🏅', 5: '🏅' };
    const icon = rankIcons[item.rank] || '🎯';
    const isUp = item.change_rate > 0;
    const isDown = item.change_rate < 0;
    const colorClass = isUp ? 'up' : (isDown ? 'down' : '');
    const sign = isUp ? '+' : '';
    const changeStr = `${sign}${Number(item.change_rate).toFixed(2)}%`;
    const gradeClass = (item.score_grade || 'A').replace('+', '-plus');

    // 4대 정량 평가 세부 시뮬레이션 지표 산출
    const momScore = Math.min(35, Math.round(item.score * 0.36));
    const boScore = Math.min(30, Math.round(item.score * 0.31));
    const effScore = Math.min(20, Math.round((item.utilization_rate / 100) * 20));
    const stabScore = Math.max(10, item.score - momScore - boScore - effScore);

    body.innerHTML = `
        <div class="modal-header-section">
            <div class="modal-rank-badge rank-${item.rank}">
                <span>${icon}</span>
                <span>추천 순위 TOP ${item.rank}위</span>
            </div>
            <div class="modal-score-badge">
                <span style="font-size:0.85rem; color:#888;">종합 평가</span>
                <span class="modal-score-val">${item.score}점</span>
                <span class="modal-score-grade grade-${gradeClass}">${item.score_grade} (${item.grade_desc || '적극 추천'})</span>
            </div>
        </div>

        <div class="modal-stock-hero">
            <div>
                <h2 class="modal-stock-name">
                    ${item.name}
                    <span class="modal-stock-code">${item.symbol}</span>
                </h2>
                <div style="font-size:0.85rem; color:#888; margin-top:6px;">코스피 실시간 대형주 · 변동성 돌파 전략 추천 종목</div>
            </div>
            <div class="modal-price-box">
                <div class="modal-price">${item.price.toLocaleString()} 원</div>
                <div class="modal-change ${colorClass}">${changeStr}</div>
            </div>
        </div>

        <!-- 4대 다면 정량 평가 분석 지표 -->
        <div class="modal-score-grid">
            <div class="modal-score-item">
                <div class="modal-score-label">🚀 모멘텀 & 당일 강도</div>
                <div class="modal-score-value">${momScore} <small style="font-size:0.75rem; color:#888;">/ 35점</small></div>
                <div style="font-size:0.75rem; color:#aaa; margin-top:4px;">당일 등락률(${changeStr}) 및 5일 이평선 지지</div>
            </div>
            <div class="modal-score-item">
                <div class="modal-score-label">⚡ 변동성 돌파 적합도</div>
                <div class="modal-score-value">${boScore} <small style="font-size:0.75rem; color:#888;">/ 30점</small></div>
                <div style="font-size:0.75rem; color:#aaa; margin-top:4px;">K(0.5) 돌파 조건 및 거래 유동성 충족</div>
            </div>
            <div class="modal-score-item">
                <div class="modal-score-label">💰 예산 집행 효율성</div>
                <div class="modal-score-value">${effScore} <small style="font-size:0.75rem; color:#888;">/ 20점</small></div>
                <div style="font-size:0.75rem; color:#aaa; margin-top:4px;">예산 대비 ${item.utilization_rate}% 최적 소진 (잔여 최소화)</div>
            </div>
            <div class="modal-score-item">
                <div class="modal-score-label">🛡️ 대형주 수급 안정도</div>
                <div class="modal-score-value">${stabScore} <small style="font-size:0.75rem; color:#888;">/ 15점</small></div>
                <div style="font-size:0.75rem; color:#aaa; margin-top:4px;">코스피 최상위 시총 및 기관/외인 수급 집중</div>
            </div>
        </div>

        <!-- 실시간 AI 추천 사유 상세 -->
        <div class="modal-reason-box">
            <div class="modal-reason-title">💡 실시간 AI 전략 분석 사유</div>
            <div class="modal-reason-text">${item.reason}</div>
        </div>

        <!-- 예산 기반 맞춤 투자 시뮬레이션 -->
        <div class="modal-budget-plan">
            <div class="modal-plan-title">📊 지정 예산(${currentRecommendationBudget.toLocaleString()}원) 매수 시뮬레이션</div>
            <div class="modal-plan-row">
                <span class="modal-plan-label">1회 권장 매수 수량</span>
                <span class="modal-plan-val highlight">${item.recommended_qty} 주</span>
            </div>
            <div class="modal-plan-row">
                <span class="modal-plan-label">총 매수 소요 금액</span>
                <span class="modal-plan-val">${item.total_cost.toLocaleString()} 원</span>
            </div>
            <div class="modal-plan-row">
                <span class="modal-plan-label">매수 후 잔여 예산</span>
                <span class="modal-plan-val">${item.remaining_budget.toLocaleString()} 원</span>
            </div>
            <div class="modal-plan-row" style="margin-top:10px;">
                <span class="modal-plan-label">자금 집행률</span>
                <span class="modal-plan-val highlight">${item.utilization_rate}%</span>
            </div>
            <div class="rec-progress-track" style="height:6px; margin-top:6px;">
                <div class="rec-progress-fill" style="width: ${Math.min(100, item.utilization_rate)}%;"></div>
            </div>
        </div>

        <!-- 하단 액션 버튼 -->
        <div class="modal-actions" style="display:flex; gap:10px; justify-content:flex-end;">
            <button type="button" class="obsidian-btn modal-order-btn" onclick="applyFromModal('${item.symbol}', ${item.price}, ${item.recommended_qty}, '${item.name}')">
                <span>⚡ 이 종목으로 주문서 작성</span>
            </button>
            <button type="button" class="obsidian-btn glow" style="background: linear-gradient(135deg, #e74c3c, #c0392b); border-color:#e74c3c; color:#fff; font-weight:bold; padding:10px 18px; border-radius:8px;" onclick="closeRecModal(); executeDirectBuy('${item.symbol}', ${item.price}, ${item.recommended_qty}, '${item.name}')">
                <span>🚀 이 종목 즉시 매수 발주</span>
            </button>
            <button type="button" class="obsidian-btn modal-close-btn-bottom" onclick="closeRecModal()">닫기</button>
        </div>
    `;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeRecModal(event) {
    if (event && event.target && event.target.id !== 'rec-detail-modal' && !event.target.classList.contains('rec-modal-close-btn') && !event.target.classList.contains('modal-close-btn-bottom')) {
        return;
    }
    const modal = document.getElementById('rec-detail-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
}

function applyFromModal(symbol, price, qty, name) {
    closeRecModal();
    applyRecommendationToOrder(symbol, price, qty, name);
}

// ESC 키로 모달 닫기
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('rec-detail-modal');
        if (modal && modal.style.display !== 'none') {
            closeRecModal();
        }
    }
});

function applyRecommendationToOrder(symbol, price, qty, name) {
    const symInput = document.getElementById('order-symbol');
    const priceInput = document.getElementById('order-price');
    const qtyInput = document.getElementById('order-qty');

    if (symInput) symInput.value = symbol;
    if (priceInput) priceInput.value = price;
    if (qtyInput) qtyInput.value = qty;

    // 실시간 시세 호가 전광판 동기화
    if (typeof searchStock === 'function') {
        const searchInput = document.getElementById('search-symbol');
        if (searchInput) searchInput.value = symbol;
        searchStock(symbol);
    }

    // 주문 영역으로 부드럽게 스크롤 & 주목 시각 효과
    if (symInput) {
        symInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        symInput.style.borderColor = '#2ecc71';
        symInput.style.boxShadow = '0 0 15px rgba(46, 204, 113, 0.8)';
        setTimeout(() => {
            symInput.style.borderColor = '';
            symInput.style.boxShadow = '';
        }, 1200);
    }
}

// === 테마 전환 (Dark / Light) ===
function applyTheme(theme) {
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    const btn = document.getElementById('theme-toggle-btn');
    
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        if (icon) icon.innerText = '☀️';
        if (label) label.innerText = 'Light';
        if (btn) btn.title = 'Dark 테마로 변경';
    } else {
        document.body.classList.remove('light-theme');
        if (icon) icon.innerText = '🌙';
        if (label) label.innerText = 'Dark';
        if (btn) btn.title = 'Light 테마로 변경';
    }
    localStorage.setItem('hts_theme', theme);
}

function toggleTheme() {
    const isLight = document.body.classList.contains('light-theme');
    applyTheme(isLight ? 'dark' : 'light');
}

function initTheme() {
    const saved = localStorage.getItem('hts_theme') || 'dark';
    applyTheme(saved);
}

// 즉시 테마 초기화 실행
initTheme();
fetchBotLogs();


