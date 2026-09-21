# ai-vibecoding-2026

바이브코딩 리포지토리

## Chapter 1

AI에게 코딩을 시키자, 제대로!

### 개념

코딩을 직접하ㄴ지는 말 것. AI와 협업해서 새로운 프로그램을 만들자

#### 기존 개발 방법

요구사항 분석 -> 설계(DB/UI 포함) -> 구현/디버깅 -> 테스트 -> 배포 -> 유지보수

#### 바이브코딩 방식

요구사항정의(PRD) -> AI 가 코드 생성/디버깅 -> 사람이 **검증**, 수정 요청, 직접 수정 -> 배포(AI) -> 유지보수(AI)

#### 핵심 포인트

- AI - 주니어/시니어 개발
- 사람 - PM + 리뷰어

### 바이브코딩 개발환경

- VS Code, VS Code Insider, Android Studio(모바일 앱 개발), ...

#### VS Code

- 채팅창 - 안씀
- 확장 패키지 - Codex, Claud Code for VS Code, Gemini Code Assist

#### Codex

- 설치 후 확장 아이콘 아래, Codex 아래 아이콘 확장

#### CLI Codex

- 파워쉘, 콘솔 창에서 명령어로 수행하는 Codex

#### 바이브 코딩

- 제로샷 프롬프트 : 아무런 기초지식없이 대화로 바이브코딩
- 원샷 프롬프트 : 적어도 한줄의 요구사항을 작성해서 바이브코딩
- 퓨샷 프롬프트 : PRD 작성을 통한 바이브코딩

### 자동매매 개발환경

토스증권 OpenAPI

- https:// corp.tossinvest.com/ko/open-api
- 토스앱 모바일 설치 가입
- 토스증권 사용 설정
- 토스증권 PC 웹사이트 동작
- 사용중인 아이피를 토스증권 PC 등록
- OpenAPI 키 발급 후 ClientID, CLient Secret 문자열 보관
- 주식 자동매매 시스템을 만들고 싶어. 근데 토스증권 API를 사용할 거야.
  https://developers.tossinvest.com/docs 이 주소에서 일단 문서 분석해줘

#### API 키 발급

- OpenAI 키 발급
- PC에서 투자하기 클릭
- 토스 앱 모바일로 인증
- ![](assets/20260921_170851_image.png)
- Client Id, Clien Secret 무조건 저장해놔야함.