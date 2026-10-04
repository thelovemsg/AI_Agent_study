# Python 핵심 문법 (Java/TS 경험자용)

## 1. 변수 & 타입

```python
# Python은 타입 선언 없이 바로 할당 (동적 타입)
name = "홍길동"          # Java: String name = "홍길동";
age = 25                 # Java: int age = 25;
is_active = True         # Java: boolean isActive = true;
salary = 3500.50         # Java: double salary = 3500.50;

# 타입 힌트 (강제는 아니지만 권장)
name: str = "홍길동"
age: int = 25
scores: list[int] = [90, 85, 70]
info: dict[str, str] = {"name": "홍길동", "city": "서울"}
```

## 2. 자료구조

```python
# 리스트 (Java: ArrayList)
fruits = ["사과", "바나나", "포도"]
fruits.append("딸기")           # add
fruits.remove("바나나")         # remove
print(fruits[0])                # 인덱싱
print(fruits[-1])               # 마지막 요소 (Python만 가능)
print(fruits[1:3])              # 슬라이싱 → ["포도", "딸기"]

# 딕셔너리 (Java: HashMap)
user = {"name": "홍길동", "age": 25}
user["email"] = "hong@test.com"  # 추가
del user["age"]                  # 삭제
print(user.get("phone", "없음")) # 키 없으면 기본값 반환

# 튜플 (불변 리스트, Java에 없음)
point = (10, 20)                 # 수정 불가

# 셋 (Java: HashSet)
tags = {"python", "java", "python"}  # 중복 제거 → {"python", "java"}
```

## 3. 조건문 & 반복문

```python
# if문 (중괄호 대신 들여쓰기)
if age >= 20:
    print("성인")
elif age >= 14:
    print("청소년")
else:
    print("어린이")

# 삼항 연산자
# Java: String result = age >= 20 ? "성인" : "미성년";
result = "성인" if age >= 20 else "미성년"

# for문
for fruit in fruits:              # Java: for (String fruit : fruits)
    print(fruit)

for i in range(5):                # Java: for (int i = 0; i < 5; i++)
    print(i)

for i, fruit in enumerate(fruits):  # 인덱스 + 값 동시에
    print(f"{i}: {fruit}")

# while문
count = 0
while count < 5:
    count += 1

# 리스트 컴프리헨션 (Python의 꽃)
# Java: list.stream().filter(x -> x > 3).map(x -> x * 2).collect(...)
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers if x > 3]  # [8, 10]
```

## 4. 함수

```python
# 기본 함수
def greet(name: str) -> str:
    return f"안녕하세요, {name}님!"

# 기본값 파라미터 (Java: 오버로딩으로 해야 함)
def create_user(name: str, age: int = 20, city: str = "서울"):
    return {"name": name, "age": age, "city": city}

create_user("홍길동")                    # age=20, city="서울" 기본값
create_user("홍길동", city="부산")        # 키워드 인자로 특정 파라미터만 지정

# *args, **kwargs (가변 인자)
def log(*args, **kwargs):
    print(args)    # 튜플: (1, 2, 3)
    print(kwargs)  # 딕셔너리: {"name": "홍길동", "age": 25}

log(1, 2, 3, name="홍길동", age=25)

# 람다 (Java: (x) -> x * 2)
double = lambda x: x * 2
```

## 5. 클래스 (OOP) - Java와 비교

### 기본 클래스

```python
# Java                              # Python
# public class Animal {             class Animal:
#     private String name;              def __init__(self, name: str, age: int):
#     private int age;                      self.name = name    # this.name = name
#                                           self.age = age
#     public Animal(String n, int a){
#         this.name = n;
#         this.age = a;              def speak(self) -> str:     # 모든 메서드 첫 인자 = self
#     }                                  return f"{self.name}이(가) 소리를 냅니다"
#
#     public String speak() {        def __str__(self) -> str:   # Java: toString()
#         return name + " speaks";       return f"Animal({self.name}, {self.age}세)"
#     }
# }

class Animal:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def speak(self) -> str:
        return f"{self.name}이(가) 소리를 냅니다"

    def __str__(self) -> str:
        return f"Animal({self.name}, {self.age}세)"

dog = Animal("멍멍이", 3)
print(dog.speak())     # 멍멍이이(가) 소리를 냅니다
print(dog)             # Animal(멍멍이, 3세)
```

### 상속

```python
# Java: public class Dog extends Animal
class Dog(Animal):
    def __init__(self, name: str, age: int, breed: str):
        super().__init__(name, age)   # Java: super(name, age);
        self.breed = breed

    def speak(self) -> str:           # 오버라이딩 (@Override 불필요)
        return f"{self.name}이(가) 멍멍!"

    def fetch(self) -> str:
        return f"{self.name}이(가) 공을 물어옵니다"

dog = Dog("바둑이", 3, "진돗개")
print(dog.speak())    # 바둑이이(가) 멍멍!
print(dog.fetch())    # 바둑이이(가) 공을 물어옵니다
```

### 접근 제어자

```python
# Java                    Python
# public                  self.name        (그냥 쓰면 public)
# private                 self.__name      (언더스코어 2개 = private 관례)
# protected               self._name       (언더스코어 1개 = protected 관례)

class BankAccount:
    def __init__(self, owner: str, balance: int):
        self.owner = owner        # public
        self._bank = "국민은행"    # protected (관례, 강제 아님)
        self.__balance = balance   # private (네임 맹글링)

    def get_balance(self) -> int:  # getter
        return self.__balance

    def deposit(self, amount: int):
        self.__balance += amount
```

### 추상 클래스 & 인터페이스

```python
from abc import ABC, abstractmethod

# Java: public abstract class Shape
# Java: public interface Drawable
# Python은 둘 다 ABC로 처리
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:       # 반드시 구현해야 함
        pass

    @abstractmethod
    def perimeter(self) -> float:
        pass

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return 3.14 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14 * self.radius
```

### 다중 상속 (Java는 불가, Python은 가능)

```python
class Flyable:
    def fly(self):
        return "날 수 있습니다"

class Swimmable:
    def swim(self):
        return "수영할 수 있습니다"

class Duck(Animal, Flyable, Swimmable):  # 다중 상속
    def speak(self) -> str:
        return f"{self.name}이(가) 꽥꽥!"
```

## 6. 매직 메서드 (Java의 특수 메서드 대응)

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):        # Java: toString()      → print() 할 때
        return f"({self.x}, {self.y})"

    def __repr__(self):       # 디버깅용 표현           → 콘솔에서 객체 찍을 때
        return f"Vector({self.x}, {self.y})"

    def __eq__(self, other):  # Java: equals()        → == 비교
        return self.x == other.x and self.y == other.y

    def __len__(self):        # Java: size()           → len() 호출 시
        return 2

    def __add__(self, other): # Java: 연산자 오버로딩 불가 → + 연산자
        return Vector(self.x + other.x, self.y + other.y)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)   # (4, 6)
print(v1 == v2)   # False
```

## 7. 예외 처리

```python
# Java: try-catch-finally → Python: try-except-finally
try:
    result = 10 / 0
except ZeroDivisionError as e:       # Java: catch (ArithmeticException e)
    print(f"에러: {e}")
except (TypeError, ValueError) as e: # 여러 예외 한번에
    print(f"에러: {e}")
except Exception as e:               # Java: catch (Exception e)
    print(f"알 수 없는 에러: {e}")
finally:
    print("항상 실행")

# 커스텀 예외
class InsufficientFundError(Exception):  # Java: extends Exception
    def __init__(self, balance, amount):
        super().__init__(f"잔액 {balance}원, 출금 {amount}원 불가")

raise InsufficientFundError(1000, 5000)
```

## 8. 데코레이터 (Java: 어노테이션과 유사하지만 더 강력)

```python
# 함수 데코레이터
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 실행시간: {time.time() - start:.2f}초")
        return result
    return wrapper

@timer                      # Java의 @Override처럼 생겼지만, 실제로 함수를 감쌈
def slow_function():
    time.sleep(1)
    return "완료"

slow_function()             # slow_function 실행시간: 1.00초

# 클래스 데코레이터
class Animal:
    @staticmethod            # Java: static 메서드
    def create_dog():
        return Animal("멍멍이", 3)

    @classmethod             # Java에 없음. 클래스 자체를 인자로 받음
    def from_string(cls, data: str):
        name, age = data.split(",")
        return cls(name, int(age))

    @property                # Java: getter를 필드처럼 접근
    def info(self) -> str:
        return f"{self.name} ({self.age}세)"

dog = Animal("멍멍이", 3)
print(dog.info)              # 메서드인데 괄호 없이 호출 가능
```

## 9. Pydantic (LangChain에서 핵심)

```python
from pydantic import BaseModel, Field
from typing import Optional

# Java: DTO/Record + 유효성 검증 라이브러리
# TypeScript: interface + zod
class UserProfile(BaseModel):
    name: str
    age: int = Field(ge=0, le=150, description="나이 (0~150)")
    email: Optional[str] = None
    tags: list[str] = []

# 자동 유효성 검증
user = UserProfile(name="홍길동", age=25)           # OK
user = UserProfile(name="홍길동", age=-1)            # ValidationError!
user = UserProfile(name="홍길동", age=25, extra="X") # 무시됨

# dict 변환
print(user.model_dump())   # {"name": "홍길동", "age": 25, "email": None, "tags": []}
```

## 10. Java → Python 빠른 대응표

| Java | Python | 비고 |
|------|--------|------|
| `public class Foo {}` | `class Foo:` | 접근제어자 없음 |
| `this.name` | `self.name` | self 명시 필수 |
| `new Foo()` | `Foo()` | new 키워드 없음 |
| `extends` | `class Dog(Animal):` | 괄호 안에 부모 클래스 |
| `implements` | 같은 방식 (ABC 사용) | 인터페이스 = 추상 클래스 |
| `@Override` | 그냥 같은 이름으로 정의 | 어노테이션 불필요 |
| `toString()` | `__str__()` | 매직 메서드 |
| `equals()` | `__eq__()` | 매직 메서드 |
| `null` | `None` | |
| `final` | 관례상 대문자 (`MAX_SIZE = 100`) | 강제 불가 |
| `System.out.println()` | `print()` | |
| `String.format()` | `f"이름: {name}"` | f-string |
| `ArrayList` | `list` | 내장 타입 |
| `HashMap` | `dict` | 내장 타입 |
| `try-catch` | `try-except` | |
| 세미콜론 `;` | 없음 | 들여쓰기로 블록 구분 |
