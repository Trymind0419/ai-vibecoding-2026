# `pip install -r ./requirements.txt`에서 `./`의 의미와 필요성

결론부터 말씀드리면, **반드시 넣을 필요는 없습니다.**
`pip install -r requirements.txt` 라고만 쓰셔도 완벽하게 똑같이 동작합니다.

## 1. `./` (점과 슬래시)의 의미
터미널(명령 프롬프트)에서 `./`는 **"현재 내가 있는 폴더(디렉토리)"**를 의미합니다.
따라서 `./requirements.txt`는 "현재 폴더 안에 있는 requirements.txt 파일"을 정확히 가리키는 표현입니다.

- `pip install -r requirements.txt` : "requirements.txt 파일을 찾아서 설치해 줘" (기본적으로 현재 폴더에서 찾음)
- `pip install -r ./requirements.txt` : "**현재 폴더에 있는** requirements.txt 파일을 설치해 줘" (위치를 명시적으로 지정)

둘 다 결과는 완전히 같기 때문에, 더 짧은 `pip install -r requirements.txt`를 사용하는 경우가 훨씬 많습니다.

## 2. 헷갈리기 쉬운 슬래시(`/`)와 역슬래시(`\`)
질문에서 '역슬래시'라고 표현해주셨지만, 적어주신 기호는 슬래시(`/`)입니다! 운영체제에 따라 폴더를 구분하는 기호가 다릅니다.

- **슬래시 (`/`)**: 맥(Mac)이나 리눅스(Linux)에서 주로 사용합니다. (예: `./requirements.txt`)
- **역슬래시 (`\`)**: 윈도우(Windows)에서 주로 사용합니다. (예: `.\requirements.txt`)
  *(참고: 한국어 윈도우 키보드에서는 역슬래시가 원화 기호(`₩`)로 표시되기도 합니다.)*

## 💡 요약
- 굳이 `./`나 `.\`를 앞에 붙이지 않아도 됩니다.
- 그냥 **`pip install -r requirements.txt`** 라고 깔끔하게 쓰시는 것을 추천해 드립니다!
