# 에이전트 메모리 (3-2) & 2_memory_base_agent.py

> 출처: 3-2) 에이전트 메모리 · 학습일 2026.10.08

## 핵심 개념

에이전트도 챗봇처럼 **대화 맥락을 기억**해야 한다. 2차 학습(Second_Langchain/3_memory)에서 `trim_messages`로 메시지를 직접 관리했다면, 여기서는 **체크포인터(Checkpointer)** 를 주입해서 프레임워크가 알아서 상태를 저장·복원하게 한다.

## 1) 체크포인터와 thread_id

### 체크포인터 주입

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools,
    checkpointer=InMemorySaver(),  # 상태 저장소 주입
)
```

`create_agent`에 `checkpointer`를 넘기면, 매 턴마다 messages 상태를 자동으로 저장한다.

### thread_id = 채팅방 열쇠

```python
cfg = {"configurable": {"thread_id": "1"}}

# 첫 번째 턴
agent.invoke({"messages": [{"role": "user", "content": "저는 Jay입니다."}]}, cfg)

# 두 번째 턴 — 같은 thread_id면 이전 대화를 기억한다
agent.invoke({"messages": [{"role": "user", "content": "제 이름이 뭐였죠?"}]}, cfg)
# → "Jay라고 하셨습니다"
```

- **같은 thread_id** → 이전 대화 이어감
- **다른 thread_id** → 완전히 새로운 세션 (기억 없음)

실무에서 thread_id에 넣을 값: `user_id`, `session_id`, `chat_room_id` 등.

### 세션 분리 확인

```python
# thread_id "2"로 바꾸면 → 이전 대화를 모른다
agent.invoke(
    {"messages": [{"role": "user", "content": "지금까지 무슨 얘기 나눴죠?"}]},
    {"configurable": {"thread_id": "2"}},
)
# → "아직 대화를 나눈 적이 없습니다"
```

### 누적된 메시지 확인

```python
for i, msg in enumerate(response["messages"], start=1):
    print(f"--- Message {i} ({msg.type}) ---")
    print(msg.content)
```

`response["messages"]`에 해당 thread의 **전체 대화 히스토리**가 누적되어 돌아온다.

## 2) InMemorySaver의 치명적 한계

`InMemorySaver`는 데이터가 **RAM에만** 머문다. 실습용으로는 괜찮지만 실무에서는 두 가지 문제가 있다.

| 문제 | 설명 |
|---|---|
| **서버 재시작 시 초기화** | 프로세스가 죽거나 재배포하면 모든 대화 기억이 증발 |
| **스케일아웃 시 끊김** | 서버 3대로 늘리면, A 서버에서 한 대화를 B 서버가 모른다 (로드밸런서가 요청을 분산하므로) |

Java/Spring으로 비유하면 — `HttpSession`에 상태를 저장하면 단일 서버에서는 되지만, 서버가 여러 대면 Redis 같은 외부 세션 저장소가 필요한 것과 같다.

## 3) 관계형 DB (PostgreSQL)로의 전환

중앙 집중식 영구 저장소로 바꾸면 위 문제를 모두 해결한다. **코드 변경은 checkpointer 한 줄뿐**이다.

```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

# 1. 중앙 DB 연결
DB_URI = "postgresql://user:password@localhost:5432/agent_db"
conn = Connection.connect(DB_URI)

# 2. RDB 기반 체크포인터 생성
db_checkpointer = PostgresSaver(conn)
db_checkpointer.setup()  # 상태 저장용 내부 테이블 자동 생성

# 3. checkpointer만 교체 — 나머지 코드는 그대로
agent = create_agent(
    model,
    tools,
    checkpointer=db_checkpointer,
)
```

### 동작 원리

- 대화 턴이 끝날 때마다 → messages 상태를 DB에 **INSERT/UPDATE**
- 새 요청이 들어오면 → thread_id를 **WHERE 조건**으로 과거 데이터를 **SELECT**

서버가 10대로 늘어나도 **동일한 DB를 바라보므로** 세션 끊김이 없고, 서버가 다운됐다 복구돼도 대화가 유지된다.

### MySQL은?

커뮤니티에서 제공하는 SQLAlchemy 기반 Saver를 쓰거나, `BaseCheckpointSaver` 인터페이스를 상속받아 직접 구현할 수 있다.

---

## 파일 구성

| 파일 | 내용 |
|---|---|
| `2_memory_base_agent.py` | InMemorySaver + thread_id로 멀티 세션 메모리 관리 |

실행:

```bash
source .venv/Scripts/activate
python 3rd_Langchain_agent_basic/2_memory_base_agent.py
```
