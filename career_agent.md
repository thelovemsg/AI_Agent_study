# 이력서 사서 (Career Agent) 설계 정리

> 2026.10.08 · LangChain Memory 학습([3_memory.md](Second_Langchain/3_memory.md))에서 출발한 실제 서비스 설계 메모

## 만들려는 것

사용자의 이력서를 **지속적으로 첨삭해주는 AI 에이전트.**

- 사용자가 이전에 어떤 질문을 했는지 기억한다
- 이력서가 완성됐는지 판단한다
- 현재 어떤 경력이 추가/수정됐는지 알려준다
- 어디를 어떻게 고치면 될지 제안한다
- 정리된 이력서를 사용자에게 출력해 보여준다

---

## 1. 해결해야 하는 문제

| # | 요구 | 그냥 만들면 생기는 문제 | 해결 방법 |
|---|---|---|---|
| 1 | 이전 질문 기억 | 대화 로그를 다 넣으면 토큰 폭발 | 질문을 **의도 태그**로 저장, 원문은 트리밍 |
| 2 | 완성도 판단 | LLM에게 매번 물으면 **답이 매번 달라짐** | 룰 기반 체크리스트를 **코드로 계산**, LLM은 설명만 |
| 3 | 변경 사항 파악 | 대화에서 추론시키면 틀림 | **revision 테이블**에 확정 diff 저장 |
| 4 | 수정 제안 | 고친 걸 또 지적함 / 거절한 걸 또 제안함 | 제안에 **상태 + 지문(fingerprint)** 부여 |
| 5 | 이력서 출력 | 통짜 텍스트로 저장해 특정 항목을 지목 못 함 | 항목마다 **id** 부여, 섹션 스키마 정의 |
| 6 | AI가 문장을 덮어씀 | 원본 소실 (치명적) | **draft → 확정** 2단계 분리 |
| 7 | 직무별 이력서 | 이력서를 복사해 두 벌 관리 → 한쪽만 수정되는 사고 | 데이터 1벌 + **layout variant** |

## 2. 핵심 결론 3가지

### (1) 기억해야 할 것은 "대화"가 아니라 "문서 상태"다

LangChain 메모리는 메시지를 누적해 다시 보내는 것이 전부다. 하지만 이력서 사서에서 중요한 정보(완성도, 변경 이력, 제안)는
**대화에서 매번 추론할 것이 아니라 DB에 확정된 값으로 들고 있어야 한다.**
→ 메모리 전략 중 **상태(State) 분리**가 주력, 대화 누적은 보조.

> 완성도를 LLM에게 대화 로그 읽혀 판단시키면 어제는 "완성됨", 오늘은 "경력 부족"이라고 답한다.
> **비결정적이면 안 되는 것을 LLM에게 맡기면 안 된다.**

### (2) 대화 기억용으로 RAG를 쓰면 안 된다

| 상황 | 방법 | RAG |
|---|---|---|
| 한 세션 안 (수십 턴) | 메시지 전체 + `trim_messages` | 불필요 |
| 세션이 매우 길어짐 | 요약본 + 최근 N턴 | 불필요 |
| 이름·목표·선호 등 영구 사실 | 구조화 테이블 → 시스템 메시지 주입 | 부적합 |
| 채용공고(JD)·합격 샘플 검색 | 벡터 검색 | **여기서만** |

이유:

- **대명사·지시어를 못 잡는다.** "제 이름이 뭐였죠?"로 검색하면 "저는 Jay입니다"는 유사도가 낮게 나온다
- **순서가 깨진다.** 대화는 시간 순서가 핵심인데 벡터 검색은 유사도 순으로 가져온다
- **직전 턴은 무조건 필요한데** 검색은 그걸 보장하지 않는다

→ RAG는 "사용자 대화를 기억하려고"가 아니라 **"외부 참고자료를 끌어오려고"** 쓴다.

### (3) 섹션 스키마는 한 곳에서만 정의한다

```
        ┌──────────────────────────────┐
        │  Experience (Pydantic 모델)   │  ← 여기서만 정의
        └──────────────────────────────┘
             │          │          │
   LLM 구조화 출력   DB 검증    템플릿 렌더링
```

세 군데에 각각 필드를 적어두면 **반드시 어긋난다.**

---

## 3. 기억의 4개 레이어

```
[A] 이력서 본체      — 구조화 저장. 항목마다 id        ← 제안을 꽂을 좌표
[B] 평가·변경 이력    — 완성도 체크, 버전별 diff        ← 코드로 계산
[C] 제안             — 생성/수락/거절/무효 상태 관리    ← 반복·모순 방지
[D] 대화             — 최근 N턴 + 요약 + 의도 태그     ← 트리밍 대상
```

## 4. DB 스키마

```sql
-- ===== [A] 이력서 본체 =====
CREATE TABLE resumes (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL,
  target_role TEXT,                        -- 평가 기준이 직무마다 다르다
  version     INT NOT NULL DEFAULT 1,      -- 수정될 때마다 증가
  updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE resume_items (
  id            BIGSERIAL PRIMARY KEY,
  resume_id     BIGINT NOT NULL REFERENCES resumes(id),
  section       TEXT NOT NULL,   -- profile | experience | project | skill | education
  sort_order    INT  NOT NULL,
  payload       JSONB NOT NULL,  -- 섹션마다 형태가 달라 JSONB
  draft_payload JSONB,           -- AI 제안 반영 초안 (NULL이면 없음)
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);
-- payload 예 (experience):
-- {"company":"A사","role":"백엔드","start":"2022-03","end":"2024-08",
--  "achievements":["결제 API 응답 420ms -> 110ms 개선"],
--  "_origin":{"achievements.0":"ai_applied","company":"user"}}

-- ===== [B] 변경 이력 =====
CREATE TABLE resume_revisions (
  id         BIGSERIAL PRIMARY KEY,
  resume_id  BIGINT NOT NULL,
  version    INT NOT NULL,
  item_id    BIGINT,
  op         TEXT NOT NULL,      -- add | update | delete
  before     JSONB,
  after      JSONB,
  source     TEXT NOT NULL,      -- user | ai_applied
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ===== [B] 완성도 평가 (버전당 1행, 코드가 계산) =====
CREATE TABLE resume_assessments (
  resume_id BIGINT NOT NULL,
  version   INT NOT NULL,
  checklist JSONB NOT NULL,      -- {"experience_has_metrics":false, ...}
  score     INT,
  PRIMARY KEY (resume_id, version)
);

-- ===== [C] 제안 =====
CREATE TABLE suggestions (
  id          BIGSERIAL PRIMARY KEY,
  resume_id   BIGINT NOT NULL,
  item_id     BIGINT,            -- NULL이면 섹션 전체 대상
  section     TEXT,
  kind        TEXT NOT NULL,     -- missing_metric | too_long | weak_verb | gap_unexplained
  severity    TEXT NOT NULL,     -- high | medium | low
  message     TEXT NOT NULL,
  fingerprint TEXT NOT NULL,     -- hash(section+kind+item_id) — 중복 생성 차단
  status      TEXT NOT NULL,     -- pending | accepted | rejected | stale
  for_version INT NOT NULL,
  resolved_at TIMESTAMPTZ,
  UNIQUE (resume_id, fingerprint, for_version)
);

-- ===== [D] 대화 =====
CREATE TABLE messages (
  id              BIGSERIAL PRIMARY KEY,
  conversation_id BIGINT NOT NULL,
  role            TEXT NOT NULL,  -- system | human | ai  <- 그대로 invoke()에 넘길 수 있게
  content         TEXT NOT NULL,
  token_count     INT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE conversation_summaries (
  conversation_id BIGINT PRIMARY KEY,
  upto_message_id BIGINT NOT NULL,
  summary         TEXT NOT NULL
);

-- "이전에 어떤 질문을 했는지" — 원문이 아니라 태그로
CREATE TABLE question_intents (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT NOT NULL,
  message_id BIGINT NOT NULL,
  intent     TEXT NOT NULL,       -- ask_length | ask_metric_phrasing | ask_gap_explain
  topic      TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ===== 렌더링 레이아웃 (데이터와 분리) =====
CREATE TABLE resume_layouts (
  id         BIGSERIAL PRIMARY KEY,
  resume_id  BIGINT NOT NULL,
  variant    TEXT NOT NULL,       -- "backend" | "devops" | "default"
  section    TEXT NOT NULL,
  sort_order INT  NOT NULL,
  visible    BOOLEAN DEFAULT true,
  label      TEXT,                -- 화면 제목 ("경력")
  UNIQUE (resume_id, variant, section)
);

CREATE TABLE resume_item_visibility (
  resume_id BIGINT NOT NULL,
  variant   TEXT   NOT NULL,
  item_id   BIGINT NOT NULL,
  visible   BOOLEAN DEFAULT true,
  PRIMARY KEY (resume_id, variant, item_id)
);
```

> `messages.role`을 `system`/`human`/`ai`로 맞춰두면 조회 결과를 **딕셔너리 그대로 `invoke()`에 밀어넣을 수 있다.**
> ([3_memory.md](Second_Langchain/3_memory.md)의 "딕셔너리 방식이 직렬화에 유리하다"가 여기서 실제 이득이 된다)

## 5. 섹션 스키마 (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union

class Experience(BaseModel):
    section: Literal["experience"] = "experience"
    company: str
    role: str
    start: str                      # "2022-03"
    end: str | None = None          # None = 재직중
    achievements: list[str] = Field(default_factory=list, max_length=5)
    tech: list[str] = Field(default_factory=list)

class Project(BaseModel):
    section: Literal["project"] = "project"
    name: str
    summary: str
    contribution: str               # 본인 기여
    tech: list[str] = Field(default_factory=list)
    link: str | None = None

class Skill(BaseModel):
    section: Literal["skill"] = "skill"
    category: str                   # "Backend", "DevOps"
    items: list[str]

class Education(BaseModel):
    section: Literal["education"] = "education"
    school: str
    major: str
    start: str
    end: str | None = None

# section 필드로 자동 분기되는 판별 유니온
ResumeItem = Annotated[
    Union[Experience, Project, Skill, Education],
    Field(discriminator="section"),
]
```

저장·조회 양쪽에서 이걸 통과시킨다.

```python
def load_items(resume_id) -> list[ResumeItem]:
    rows = db.query("SELECT section, payload FROM resume_items "
                    "WHERE resume_id = %s ORDER BY sort_order", resume_id)
    return [TypeAdapter(ResumeItem).validate_python({**r.payload, "section": r.section})
            for r in rows]
```

## 6. 턴마다 돌아가는 흐름

```python
def build_prompt(user_id, resume_id, conversation_id, user_input):
    # (1) 코드로 계산 — 결정적이어야 하므로 LLM에 맡기지 않는다
    resume      = load_resume(resume_id)                # [A]
    assessment  = assess(resume)                        # [B] 룰 기반 체크리스트
    recent_diff = load_revisions(resume_id, last_n=5)   # [B]
    open_sugg   = load_suggestions(resume_id, status="pending", limit=5)   # [C]
    rejected    = load_fingerprints(resume_id, status="rejected")          # [C]
    asked       = top_intents(user_id, limit=5)         # [D]

    # (2) 시스템 메시지에 '상태'를 고정 주입 -> 트리밍에 잘려나가지 않는다
    system = f"""당신은 이력서 첨삭 전문가입니다.

[이력서 현황] 목표 직무: {resume.target_role} / 버전 v{resume.version}
{render_outline(resume)}

[완성도] {assessment.score}/100
미충족 항목: {render_unmet(assessment)}

[최근 변경]
{render_diff(recent_diff)}

[미해결 제안]
{render_suggestions(open_sugg)}

[이미 거절된 제안 — 다시 제안하지 말 것]
{render_rejected(rejected)}

[사용자가 이전에 물어본 주제]
{", ".join(asked)}  <- 이미 설명한 내용은 반복하지 말고 심화해서 답하라
"""

    # (3) 대화는 트리밍해서 뒤에 붙인다
    trimmed = trim_messages(
        load_messages(conversation_id),
        strategy="last", token_counter=count_tokens_approximately,
        max_tokens=1500, include_system=False, start_on="human",
    )

    return [{"role": "system", "content": system}, *trimmed,
            {"role": "human", "content": user_input}]
```

## 7. 놓치기 쉬운 설계 포인트

### diff는 코드로, 설명은 LLM으로

"어떤 경력이 추가됐는지"를 대화 로그에서 추론시키면 틀린다. `resume_revisions`의 확정 diff를 **문장으로 풀어주는 일만** LLM에 맡긴다.

### 제안에 `stale` 상태가 반드시 필요하다

사용자가 A사 경력을 수정하면 A사에 걸린 pending 제안은 무효가 된다. 버전이 올라갈 때 무효화하지 않으면
**"이미 고쳤는데 또 같은 지적을 하는"** 최악의 UX가 된다.

```sql
UPDATE suggestions SET status = 'stale'
WHERE resume_id = :id AND item_id = :changed_item AND status = 'pending';
```

### 거절 지문(fingerprint)을 기억한다

"경력 공백은 설명 안 하겠다"고 거절했으면 다시 제안하면 안 된다.
`fingerprint`로 중복을 막고, 거절 목록을 프롬프트에 **금지 사항으로 명시**한다.

### 제안 생성은 대화 응답과 분리한다

제안은 턴마다가 아니라 **이력서가 변경됐을 때만** 별도 호출로 생성 → DB 저장 → 이후 턴에서는 읽어 쓰기만 한다.
대화 10턴 동안 제안 생성 호출이 1~2회로 줄어 **비용이 크게 떨어진다.**

```python
class Suggestion(BaseModel):
    item_id: int | None
    section: str
    kind: str
    severity: Literal["high", "medium", "low"]
    message: str

suggestions = model.with_structured_output(list[Suggestion]).invoke(review_prompt)
```

### draft → 확정 2단계

AI 제안을 수락하면 바로 본문에 쓰지 않고 `draft_payload`에 넣어 미리보기를 보여준다.

| 상태 | `payload` | `draft_payload` | 화면 |
|---|---|---|---|
| 평시 | 확정본 | NULL | 확정본만 |
| 제안 반영 직후 | 확정본 **유지** | AI 수정안 | 좌: 기존 / 우: 변경안 (diff) |
| 사용자 확정 | 초안으로 교체 | NULL | 새 확정본 + revision 기록 |

> **LLM이 멋대로 문장을 바꿔 원본이 사라지는 것이 이 서비스에서 가장 치명적인 사고다.**

### 필드 단위 출처 추적

`payload._origin`에 필드별 출처(`user` / `ai_applied`)를 담아두면, 제출 전에 **AI가 손댄 부분만 검토**할 수 있다.
사실관계가 중요한 문서에서는 필요한 장치.

## 8. 렌더링 설계

출력 포맷마다 로직을 따로 쓰지 말고 **중간 표현(ViewModel)에서 갈라지게** 한다.

```
resume_items (DB)
      ├─ load + validate  (Pydantic)
      ├─ variant 필터     (layout / visibility)
      ├─ 정렬             (sort_order, 날짜 역순)
      ▼
  ResumeView  ← 여기까지 공통
      ├──► to_dict()  → JSON      (웹 화면, React)
      ├──► Jinja2 .md → Markdown  (복사/붙여넣기, LLM 입력)
      └──► Jinja2 .html → HTML → WeasyPrint → PDF (제출용)
```

```python
@dataclass
class RenderedSection:
    key: str                  # "experience"
    label: str                # "경력"
    items: list[ResumeItem]
    unmet: list[str]          # 이 섹션의 미충족 체크리스트
    suggestions: list[dict]   # 이 섹션에 걸린 제안

@dataclass
class ResumeView:
    target_role: str
    version: int
    sections: list[RenderedSection]
    score: int

def build_view(resume_id, variant="default", with_feedback=True) -> ResumeView:
    items  = load_items(resume_id)
    layout = load_layout(resume_id, variant)
    hidden = load_hidden_item_ids(resume_id, variant)

    sections = []
    for row in layout:
        if not row.visible:
            continue
        picked = [i for i in items if i.section == row.section and i.id not in hidden]
        sections.append(RenderedSection(
            key=row.section,
            label=row.label or DEFAULT_LABELS[row.section],
            items=picked,
            unmet=unmet_for(resume_id, row.section) if with_feedback else [],
            suggestions=suggestions_for(resume_id, row.section) if with_feedback else [],
        ))
    return ResumeView(...)
```

`with_feedback` 하나로 **같은 ViewModel에서 두 화면**을 만든다.

| 용도 | `with_feedback` | 결과 |
|---|---|---|
| 첨삭 화면 | `True` | 항목 옆에 제안 배지, 빈 항목에 "여기 채우세요" |
| 제출용 PDF | `False` | 피드백 전부 제거, 순수 이력서 |

### 제안을 본문에 겹쳐 보여주기

`suggestions.item_id` 앵커가 여기서 회수된다. 통짜 텍스트로 저장했다면 "경력 세 번째 항목"을 지목할 좌표가 없어 불가능하다.

```html
{% for item in section.items %}
  <div class="item" id="item-{{ item.id }}">
    <h3>{{ item.company }} · {{ item.role }}</h3>
    <span class="period">{{ item.start }} ~ {{ item.end or '재직중' }}</span>
    <ul>{% for a in item.achievements %}<li>{{ a }}</li>{% endfor %}</ul>

    {% for s in section.suggestions if s.item_id == item.id %}
      <div class="suggest {{ s.severity }}">
        {{ s.message }}
        <button data-sugg="{{ s.id }}" data-act="accept">반영</button>
        <button data-sugg="{{ s.id }}" data-act="reject">무시</button>
      </div>
    {% endfor %}
  </div>
{% endfor %}
```

### 출력 포맷 선택

| 용도 | 포맷 | 이유 |
|---|---|---|
| 웹 화면 | **JSON** | 서버에서 HTML을 내리면 React에서 제안 배지를 다루기 어렵다 |
| 전체 리뷰 LLM 입력 | **Markdown** | JSON보다 토큰이 적고 모델이 더 잘 읽는다 |
| 제출 | **PDF** | HTML → WeasyPrint |

### 직무별 변형

경력 데이터는 **한 벌만** 유지하고 `resume_layouts.variant`로 백엔드용/DevOps용을 각각 출력한다.
이력서를 복사해 두 벌 관리하면 **한쪽만 고치는 사고가 반드시 난다.**

## 9. 토큰 관리

이력서 전문을 매 턴 넣으면 금방 터진다.

| 넣는 것 | 형태 |
|---|---|
| 전체 이력서 | **목차 + 섹션별 통계만** (항목 수, 분량, 충족 여부) |
| 지금 작업 중인 섹션 | **원문 전체** |
| 나머지 섹션 | 제목만 |

사용자가 "경력 부분 봐주세요"라고 하면 그 섹션만 원문으로 펼친다.

## 10. RAG를 쓸 자리

대화 기억용으로는 필요 없다. 쓸 자리는 따로 있다.

- 지원 회사의 **채용공고(JD)** 검색 → 이력서와 매칭
- **합격 이력서 샘플 / 직무별 레퍼런스** 코퍼스에서 유사 사례 검색
- 사용자가 과거에 쓴 **다른 버전 이력서·포트폴리오 원문** 검색

---

## 11. 아직 결정하지 않은 것

- [ ] 완성도 체크리스트 항목 확정 (직무별로 다르게 할지)
- [ ] `question_intents.intent` 태그 집합 정의 + 분류 방법 (룰 vs LLM)
- [ ] 요약 트리거 시점 (N턴마다 / 토큰 임계값 초과 시)
- [ ] DB 선택 (현재 문서는 PostgreSQL JSONB 기준)
- [ ] 제안 생성 프롬프트 설계 및 품질 검증 방법
