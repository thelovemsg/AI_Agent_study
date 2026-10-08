# 초기 세팅 (SETUP)

> **새 PC나 새로 clone한 폴더에서는 아래 과정을 먼저 거쳐야 실행됩니다.**
> 기존에 쓰던 내 PC에서는 2~5번이 이미 끝나 있으므로 [매번 작업 시작할 때](#매번-작업-시작할-때)만 하면 됩니다.

**목차**

- [왜 가상환경(venv)을 쓰는가](#왜-가상환경venv을-쓰는가) — 개념, Java/Node와의 비교
- [왜 새 환경마다 다시 만들어야 하는가](#왜-새-환경마다-다시-만들어야-하는가) — gitignore 때문
- [세팅 순서 1~6](#1-저장소-받기) — 실제 명령어
- [매번 작업 시작할 때](#매번-작업-시작할-때)
- [자주 겪는 문제](#자주-겪는-문제)

## 왜 가상환경(venv)을 쓰는가

### 한 줄 요약

Python은 **기본적으로 패키지를 PC 전체에 하나로 설치**하기 때문에, 프로젝트별로 격리해 줄 장치가 따로 필요합니다. 그게 가상환경입니다.

### Java / Node에는 왜 이 단계가 없었나

| | 의존성이 설치되는 곳 | 프로젝트별 격리 |
|---|---|---|
| Java (Maven/Gradle) | `~/.m2`에 여러 버전이 공존, 빌드 시 `pom.xml`이 지정한 버전만 classpath에 올림 | **빌드 도구가** 해줌 |
| Node (npm) | 프로젝트 안의 `node_modules/` | **구조 자체가** 프로젝트 로컬 |
| Python (pip) | Python 설치 폴더의 `site-packages/` 한 곳 | **없음 → 직접 만들어야 함** |

Java는 `~/.m2`에 같은 라이브러리의 여러 버전이 있어도 프로젝트마다 classpath를 다르게 구성합니다. Node는 애초에 프로젝트 폴더 안에 받습니다.
반면 **pip은 `python/Lib/site-packages/`에 설치하고, 그곳에는 패키지당 버전이 하나만 존재할 수 있습니다.**

### venv 없이 쓰면 생기는 일

```
이 프로젝트          : langchain 0.3 필요
나중에 볼 다른 예제   : langchain 0.1 기준 코드

pip install langchain==0.1   ← 이 순간 0.3이 덮어써짐
→ 이 프로젝트가 깨짐
```

Python에는 "프로젝트별 버전"이라는 개념이 없어서, 한쪽을 설치하면 **다른 쪽이 조용히 망가집니다.**
LangChain은 특히 버전마다 API가 크게 바뀌어서(`langchain.chat_models` → `langchain_openai` 같은 모듈 이동) 이 문제를 빠르게 만나게 됩니다.

### venv가 실제로 하는 일

`python -m venv .venv`는 `.venv/` 안에 **python.exe · pip · site-packages를 한 세트로 복제**합니다.

```
.venv/
├── Scripts/
│   ├── python.exe      ← 이 프로젝트 전용 인터프리터
│   └── pip.exe
└── Lib/site-packages/  ← 이 프로젝트 전용 패키지 (node_modules 역할)
```

`activate`가 하는 일은 딱 하나, **PATH 맨 앞에 `.venv/Scripts`를 끼워넣는 것**입니다.
그 뒤로 `python`, `pip`을 입력하면 전역이 아니라 이 폴더의 것이 실행됩니다. 그래서:

- `pip install`한 결과가 PC 전체가 아니라 `.venv` 안에만 들어간다
- 환경이 꼬이면 `.venv` 폴더만 지우고 다시 만들면 된다 (전역 Python은 무사)
- `deactivate`하면 PATH가 원래대로 돌아온다

> 비유하면 **`.venv` = `node_modules` + 전용 node 바이너리**입니다.

### 이 PC 환경에서는 사실상 필수

현재 `python`이 Microsoft Store 버전(`AppData\Local\Microsoft\WindowsApps\python`)으로 잡혀 있습니다.
이쪽은 설치 폴더가 보호되어 있어서 전역 `pip install`이 권한 오류를 내거나, 설치는 됐는데 import가 안 되는 식으로 어긋나는 경우가 흔합니다.
최근 Python 및 Linux 배포판은 전역 설치를 아예 차단하기도 합니다(`error: externally-managed-environment`). venv를 쓰면 이 문제가 전부 사라집니다.

### 그래서 requirements.txt도 함께 필요하다

venv는 "패키지를 어디에 담을지"만 해결합니다. **"어떤 패키지를 쓰는지" 기록은 Python에서 자동으로 생기지 않습니다.**
`pom.xml` / `package.json`에 해당하는 역할을 `requirements.txt`가 손으로 대신합니다.

| Java | Node | Python |
|---|---|---|
| `pom.xml` | `package.json` | `requirements.txt` (수동 작성) |
| `~/.m2` + classpath | `node_modules/` | `.venv/Lib/site-packages/` |
| `mvn install` | `npm install` | `pip install -r requirements.txt` |

---

## 왜 새 환경마다 다시 만들어야 하는가

`.gitignore`에 아래 두 개가 들어 있어서 **git에 올라가지 않습니다.**

```
.venv/    # 가상환경 (용량이 크고, OS/경로에 종속적이라 공유 불가)
.env      # API 키 (절대 올려서는 안 되는 비밀 정보)
```

즉 `git clone`으로 받은 폴더에는 **가상환경도, API 키도 없습니다.** 코드(`.py`, `.md`)만 들어옵니다.
그래서 새 환경에서 바로 activate를 하면 이렇게 실패합니다.

```bash
$ source .venv/Scripts/activate
bash: .venv/Scripts/activate: No such file or directory   # ← 파일이 없는 게 정상
```

경로 오타가 아니라 **아직 만들지 않았기 때문**입니다. 아래 순서대로 한 번만 만들어 주면 됩니다.

---

## 1. 저장소 받기

```bash
git clone <저장소 주소>
cd AI_Agent_study
```

## 2. 가상환경 생성 (최초 1회)

```bash
python -m venv .venv
```

- `python`이 안 먹히면 `py -m venv .venv` 로 Python 런처를 사용합니다.
- 이 명령이 `.venv/` 폴더를 만들어 줍니다. 이게 끝나야 다음 단계의 activate가 동작합니다.

## 3. 가상환경 활성화

**셸마다 명령이 다릅니다.** 쓰는 터미널에 맞춰 사용하세요.

| 셸 | 명령 |
|---|---|
| Git Bash / MINGW64 | `source .venv/Scripts/activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| cmd | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

성공하면 프롬프트 앞에 `(.venv)`가 붙습니다.

```bash
(.venv) sjmoon@sjmoon MINGW64 /c/work/projects/AI_Agent_study (main)
$
```

> **Git Bash에서는 `source`를 빼면 안 됩니다.** `.venv/Scripts/activate` 만 입력하면
> 활성화가 현재 셸에 적용되지 않거나 권한 오류가 납니다.

## 4. 패키지 설치

```bash
pip install openai python-dotenv langchain langchain-openai
```

설치 후 목록을 남겨 두면 다음 환경에서 한 줄로 복구할 수 있습니다.

```bash
pip freeze > requirements.txt     # 기록
pip install -r requirements.txt   # 복구
```

## 5. `.env` 파일 만들기

프로젝트 루트에 `.env`를 새로 만들고 키를 넣습니다.

```
OPEN_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_pt_...   # 4차 학습(LangSmith)부터 필요. 없으면 추적만 꺼진다
```

> **키 이름이 `OPENAI_API_KEY`가 아니라 `OPEN_API_KEY`입니다.**
> 이 프로젝트의 스크립트는 `os.environ["OPEN_API_KEY"]`로 직접 읽어서
> `ChatOpenAI(api_key=...)`에 넘기고 있습니다. 이름을 바꾸면 `KeyError`가 납니다.

## 6. 동작 확인

```bash
python First/study1.py
```

---

## 매번 작업 시작할 때

세팅이 끝난 환경에서는 **3번(활성화)만** 하면 됩니다.

```bash
cd /c/work/projects/AI_Agent_study
source .venv/Scripts/activate
```

작업을 끝낼 때는 `deactivate`.

---

## 자주 겪는 문제

| 증상 | 원인 / 해결 |
|---|---|
| `.venv/Scripts/activate: No such file or directory` | 가상환경이 없음 → 2번부터 다시 |
| `bash: .venv/Scripts/activate: Permission denied` | `source`를 빼고 실행함 → `source` 붙여서 실행 |
| PowerShell에서 `이 시스템에서 스크립트를 실행할 수 없으므로` | 실행 정책 제한 → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `python -m venv` 가 조용히 실패하거나 경로가 꼬임 | Microsoft Store 버전 Python(`WindowsApps\python`)의 알려진 문제 → `py -m venv .venv` 또는 python.org 정식 설치본 사용 |
| `ModuleNotFoundError: No module named 'langchain'` | 가상환경을 활성화하지 않았거나 4번을 건너뜀 |
| `KeyError: 'OPEN_API_KEY'` | `.env`가 없거나 키 이름이 다름 → 5번 확인 |
