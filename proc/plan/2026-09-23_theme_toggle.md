# [작업 계획] 테마 변경 토글 버튼 (Dark / Light) 구현

## 1. 요구사항 분석
- **목적**: Dark 테마와 Light 테마를 자유롭게 전환할 수 있는 기능 제공
- **위치**: 화면 우측 하단에 고정된 Floating Action Button (FAB)
- **상태 보존**: 브라우저 `localStorage`에 테마 설정 저장하여 페이지 새로고침 시에도 유지

## 2. 작업 단계 및 완료 내역
1. [x] **CSS 테마 확장 (`auto_trader/static/style.css`)**:
   - 우측 하단 플로팅 토글 버튼 스타일 (`.theme-floating-btn`) 정의
   - `body.light-theme` 클래스 기반의 밝은 테마 색상(패널, 헤더, 전광판, 텍스트, 테이블, 버튼, 폼 인풋 등) 전면 재정의
2. [x] **HTML 버튼 추가 (`auto_trader/static/index.html`)**:
   - 우측 하단 플로팅 토글 버튼 DOM 추가
   - 스크립트 캐시 버전 갱신 (`script.js?v=5.0`)
3. [x] **JS 테마 로직 (`auto_trader/static/script.js`)**:
   - `toggleTheme()` 함수 구현 (Dark ↔ Light 토글)
   - `initTheme()` 함수로 페이지 로드 시 저장된 테마 불러오기 (`localStorage` 연동)
4. [x] **검증 및 스크린샷 확인**:
   - Playwright로 Dark 테마 및 Light 테마 전환 렌더링 확인 완료 (`dark_theme_fab_proof.png`, `light_theme_30_proof.png`)
   - 토글 버튼 위치 및 UI 상태 스크린샷 캡처 완료
