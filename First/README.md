# AI Agent 학습 일지

## 1차 - 2026.10.03

### 오늘 한 것
- Windows + VS Code + Git Bash 환경에서 실습 환경 첫 세팅
- OpenAI API를 활용한 첫 번째 Python 스크립트(`study1.py`) 작성
- `.env` 파일에서 API 키를 불러와 안전하게 사용하는 방법 학습
- `python-dotenv` 패키지를 활용한 환경변수 관리
- `gpt-4.1-nano` 모델로 간단한 질의응답 테스트

---

### 실습 환경 세팅 정리

「AI 에이전트는 이렇게 만든다」 실습을 Colab 대신 내 PC의 VS Code에서 하기 위한 세팅.

- 실습 폴더: `D:\study\AI_Agent`
- 터미널: Git Bash (MINGW64)
- Python: 3.13

#### 전체 그림

책은 Google Colab(브라우저에서 돌아가는 주피터 노트북)을 쓴다. 우리는 같은 걸 내 PC에서 하려는 것이고, 그러려면 아래 4가지가 필요하다.

| 필요한 것 | 역할 | Java로 비유하면 |
|---|---|---|
| Python | 코드를 실행하는 본체 | JDK |
| 가상환경 (`.venv`) | 이 프로젝트 전용 라이브러리 보관함 | 프로젝트별 의존성 (전역 설치 방지) |
| pip | 라이브러리 설치 도구 | Maven / Gradle |
| VS Code + Jupyter 확장 | `.ipynb` 노트북을 열고 셀 단위로 실행 | IntelliJ |

흐름:

```
폴더 열기 -> 확장 설치 -> 가상환경 만들기 -> 라이브러리 설치
-> 키 파일(.env) 준비 -> 노트북 열기 -> 커널 선택 -> 실행
```

한 번만 해두면 다음부터는 "매일 시작할 때"만 보면 된다.

---

#### 1. VS Code에서 실습 폴더 열기

1. VS Code 실행
2. **파일 > 폴더 열기** (`Ctrl+K` → `Ctrl+O`)
3. `D:\study\AI_Agent` 선택
4. "이 폴더의 작성자를 신뢰합니까?" → **예**

> 파일 하나가 아니라 **폴더**를 여는 게 중요하다. VS Code는 연 폴더를 프로젝트 루트로 인식한다.

#### 2. 확장 프로그램 설치

`Ctrl+Shift+X`에서 아래 두 개 설치 (제작자 Microsoft 확인):
- **Python**
- **Jupyter**

#### 3. 터미널 열기

`` Ctrl+` `` → 터미널 패널 우측 `+` 옆 화살표 → **Git Bash** 선택

```
thelo@DESKTOP-9B1HFUA MINGW64 /d/study/AI_Agent (main)
$
```

#### 4. 가상환경 만들기와 활성화

```bash
# 만들기 (최초 1회)
python -m venv .venv

# 활성화 (터미널 열 때마다)
source .venv/Scripts/activate
```

`(.venv)`가 프롬프트 앞에 붙으면 성공.

> 터미널 종류마다 활성화 명령이 다르다:
>
> | 터미널 | 명령 |
> |---|---|
> | Git Bash | `source .venv/Scripts/activate` |
> | PowerShell | `.venv\Scripts\Activate.ps1` |
> | cmd | `.venv\Scripts\activate.bat` |

#### 5. 라이브러리 설치

```bash
python -m pip install openai ipykernel python-dotenv
```

| 패키지 | 용도 |
|---|---|
| `openai` | OpenAI API 호출 |
| `ipykernel` | VS Code가 `.venv`의 Python으로 노트북을 실행하게 해주는 연결 부품 |
| `python-dotenv` | `.env` 파일에서 API 키를 읽어옴 |

> `pip install` 대신 `python -m pip install`을 쓰는 이유: 활성화된 Python의 pip이 확실히 실행됨. 그냥 `pip`은 전역 pip이 잡혀서 Permission denied가 날 수 있다.

#### 6. .gitignore

```
.venv/
.env
__pycache__/
.ipynb_checkpoints/
```

| 항목 | 제외 이유 |
|---|---|
| `.venv/` | 용량이 크고, 다른 PC에서는 새로 만들면 됨 |
| `.env` | API 키가 들어 있음. 공개되면 과금됨 |
| 나머지 | 자동 생성 캐시 |

#### 7. API 키를 .env에 넣기

폴더 최상위에 `.env` 파일 생성 (따옴표 없이, `=` 양옆 공백 없이):

```
OPENAI_API_KEY=sk-proj-본인키
```

책에서는 `os.environ["OPENAI_API_KEY"] = "sk-proj-xxx"`로 직접 적지만, push할 때 키가 같이 올라가므로 `.env`로 분리한다.

#### 8. 노트북 커널 선택 (자주 막히는 부분)

1. `.ipynb` 파일 열기
2. 우측 상단 **"커널 선택"** 클릭
3. **Python 환경...** → `.venv` 항목 선택

안 보이면: `Ctrl+Shift+P` > `Python: Select Interpreter` > `.venv` 선택

#### 9. 책 코드와 달라지는 부분

| 책 (Colab) | VS Code |
|---|---|
| `!pip install openai` 셀 | 건너뜀 (이미 설치). 셀에서 하려면 `%pip install 패키지명` |
| `os.environ["OPENAI_API_KEY"] = "..."` | `load_dotenv()`로 대체 |
| `from google.colab import ...` | 로컬에서는 동작 안 함. 나오면 그 부분만 수정 |

#### 10. 매일 시작할 때

1. VS Code로 폴더 열기
2. `.ipynb` 파일 열기 (커널은 한 번 선택하면 기억됨)
3. 맨 위 `load_dotenv()` 셀부터 순서대로 실행

새 라이브러리 설치 시:

```bash
source .venv/Scripts/activate
python -m pip install 패키지명
```

---

### 새로 배운 개념

1. **환경변수 관리**: API 키를 코드에 직접 넣지 않고 `.env` 파일 + `python-dotenv`로 관리
2. **OpenAI Responses API**: `client.responses.create()`를 사용한 API 호출 방법
3. **모델별 파라미터 차이**: 모든 모델이 같은 옵션을 지원하지 않음 (아래 참고)

---

### 주의사항: 모델별 reasoning 지원 여부

`reasoning` 파라미터는 **추론(thinking) 기능을 지원하는 모델에서만** 사용 가능하다.

| 모델 | reasoning 지원 | 비고 |
|------|---------------|------|
| o1 | O | `reasoning.effort`: low, medium, high |
| o1-mini | O | `reasoning.effort`: low, medium, high |
| o3 | O | `reasoning.effort`: low, medium, high |
| o3-mini | O | `reasoning.effort`: low, medium, high |
| o4-mini | O | `reasoning.effort`: low, medium, high |
| gpt-4.1 | X | reasoning 파라미터 사용 시 에러 발생 |
| gpt-4.1-mini | X | reasoning 파라미터 사용 시 에러 발생 |
| gpt-4.1-nano | X | reasoning 파라미터 사용 시 에러 발생 |

> **핵심**: 모델마다 지원하는 옵션이 다르므로, API 호출 전에 해당 모델이 어떤 파라미터를 지원하는지 반드시 확인해야 한다. 지원하지 않는 파라미터를 넣으면 `400 BadRequestError`가 발생한다.

---

### 에러 경험

```
openai.BadRequestError: Error code: 400
"Unsupported parameter: 'reasoning.effort' is not supported with this model."
```
- `gpt-4.1-nano`에 `reasoning={"effort": "low"}`를 넣어서 발생
- 해결: `reasoning` 파라미터를 제거하거나, reasoning을 지원하는 모델(o 시리즈)로 변경

---

### 자주 나는 에러 모음

| 증상 | 원인 | 해결 |
|---|---|---|
| `bash: .venvScriptsactivate: command not found` | Git Bash에서 백슬래시 사용 | `source .venv/Scripts/activate` |
| `bash: !pip: event not found` | `!`는 노트북 셀 전용 문법 | 터미널에서는 `!` 없이 입력 |
| `pip: Permission denied` | 가상환경 미활성화 상태 | 활성화 후 `python -m pip install ...` |
| `ModuleNotFoundError` | 노트북 커널이 `.venv`가 아님 | 커널 선택 다시 |
| `load_dotenv()`가 `False` | `.env` 위치나 이름이 틀림 | 폴더 최상위에 있는지, `.env.txt`가 아닌지 확인 |
| `AuthenticationError` / 401 | 키가 틀렸거나 안 읽힘 | `.env` 내용 확인 후 커널 재시작 |
| 코드 고쳤는데 반영 안 됨 | 이전 변수가 메모리에 남음 | 노트북 **다시 시작(Restart)** 후 재실행 |
