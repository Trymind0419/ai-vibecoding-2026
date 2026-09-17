# Antigravity & Gemini 규칙 (SPARK + IPO 체계)

이 프로젝트(`D:\SourceBank\ai-vibecoding-2026`)는 **SPARK-Harness-AI_Agent_VibeCoding** 프로세스를 기본 개발 및 작업 규약으로 준수합니다.

---

## 1. 기본 원칙
- **작업 프로세스**: 사용자의 모든 작업 요청은 **SPARK (Spec, Plan, Archive, Research, Knowhow)** 프로세스를 기반으로 진행합니다.
- **결과물 위치**: 모든 생성물과 결과물은 `D:\SourceBank\ai-vibecoding-2026` 프로젝트 폴더 내 **IPO (Input, Proc, Output, Data, Src)** 구조에 맞추어 생성합니다.

---

## 2. SPARK 명령 처리 체계 (`proc/`)
- `proc/spec/` : **S (설계 명세)** — 기능 명세서, 아키텍처, 규칙 문서
- `proc/plan/` : **P (작업 계획)** — 작업 단계별 계획서 (체크리스트 및 진행 상태 기록)
- `proc/research/` : **R (사전 조사)** — 구현 전 기술 스택/라이브러리 조사 및 비교 분석 문서
- `proc/archive/` : **A (비활성 문서)** — 대화 이력, 지난 프롬프트 로그 (명시적 지시 없이 직접 참조하지 않음)
- `proc/knowhow/` : **K (재사용 지식)** — 반복 사용 가능한 프롬프트 및 노하우 (명시적 지시 없이 직접 참조하지 않음)

---

## 3. IPO 데이터 및 소스코드 구조
- `input/` : 입력 데이터, 참고 문서/데이터 (명시적 지시 없이 수정하지 않음)
- `proc/` : 명령 처리 및 프로세스 관리 문서
- `output/` : 최종 산출물 및 데이터 처리 결과물
- `data/` : 개발용 영구 데이터 (SQLite DB 파일 등)
- `src/` : 실제 프로그램 소스 코드

---

## 4. 작업 시 필수 행동 수칙
1. **작업 전 계획 수립**: 복잡한 작업이나 새로운 구현 요청 시 먼저 `proc/plan/`에 계획 문서를 작성/업데이트하고 단계별로 구현합니다.
2. **사전 리서치 필요 시**: 기술 검토나 설계 비교가 필요한 경우 `proc/research/`에 리서치 문서를 먼저 기록합니다.
3. **명세 관리**: 신규 요구사항이나 설계 변경 시 `proc/spec/` 문서를 동기화합니다.
4. **결과물 저장**:
   - 실행 가능한 소스코드는 `src/` 하위에 배치합니다.
   - 데이터나 최종 산출 파일은 `output/`에 배치합니다.
5. **스킬 활용**: `.agents/skills/`에 정의된 5대 핵심 스킬(`/create-spec`, `/update-plan`, `/update-spec`, `/update-research`, `/init-project`)을 적극 활용합니다.

