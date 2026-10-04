# Java 어노테이션 원리 & 동작 시점 정리

## 어노테이션의 본질

**어노테이션 = 스티커 (메타데이터)**

```java
@NotNull
private String name;
```

어노테이션 자체는 아무 로직도 실행하지 않는다. "여기에 표시해둘게"일 뿐이다.
**그 스티커를 읽는 누군가(프레임워크, 컴파일러, 내 코드)가 실제 처리를 한다.**

---

## 1단계: 어노테이션은 언제까지 살아있나? (@Retention)

> 📎 공식 문서: [java.lang.annotation.Retention](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/Retention.html)
>
> *"Indicates how long annotations with the annotated type are to be retained.
> If no Retention annotation is present on an annotation type declaration, the retention policy defaults to RetentionPolicy.CLASS."*

어노테이션에도 수명이 있다. "이 스티커를 언제까지 유지할 건지" 결정하는 게 `@Retention`.
**@Retention을 안 붙이면 기본값은 CLASS다.** (실행 중에 못 읽음 → 보통 의도한 게 아님)

```java
@Retention(RetentionPolicy.SOURCE)   // 컴파일 전에 사라짐
@Retention(RetentionPolicy.CLASS)    // .class 파일까지만 살아있음 (기본값)
@Retention(RetentionPolicy.RUNTIME)  // 실행 중에도 살아있음 (가장 많이 씀)
```

> 📎 공식 문서: [java.lang.annotation.RetentionPolicy](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/RetentionPolicy.html)

| Retention | 공식 설명 (원문) | 누가 읽나 | 예시 |
|-----------|-----------------|----------|------|
| `SOURCE` | *Annotations are to be discarded by the compiler.* | 컴파일러 | `@Override`, `@SuppressWarnings`, Lombok(`@Getter`) |
| `CLASS` | *Annotations are to be recorded in the class file by the compiler but need not be retained by the VM at run time.* | 바이트코드 분석 도구 | 거의 안 씀 |
| `RUNTIME` | *Annotations are to be recorded in the class file by the compiler and retained by the VM at run time, so they may be read reflectively.* | 리플렉션, Spring, JPA 등 | `@Autowired`, `@Entity`, `@NotNull` |

> 우리가 쓰는 대부분의 어노테이션은 **RUNTIME**이다. 실행 중에 리플렉션으로 읽어야 하니까.

### Retention 선택 기준

| 내 어노테이션이... | Retention | 이유 |
|-------------------|-----------|------|
| 컴파일러한테만 알려주면 됨 | `SOURCE` | 실행 시 필요 없음 |
| 실행 중에 리플렉션으로 읽어야 함 | `RUNTIME` | Spring, 검증, 커스텀 처리 등 |
| 잘 모르겠음 | `RUNTIME` | 거의 항상 RUNTIME이 맞음 |

---

## 2단계: 어노테이션을 어디에 붙일 수 있나? (@Target)

> 📎 공식 문서: [java.lang.annotation.Target](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/Target.html)
>
> *"Indicates the contexts in which an annotation type is applicable."*
>
> **@Target을 안 붙이면 타입 파라미터 선언을 제외한 모든 곳에 붙일 수 있다.**

> 📎 공식 문서: [java.lang.annotation.ElementType](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/ElementType.html)

| ElementType | 공식 설명 (원문) | 한글 | 예시 |
|-------------|-----------------|------|------|
| `TYPE` | *Class, interface (including annotation type), or enum declaration* | 클래스/인터페이스/enum | `@Entity`, `@Component` |
| `FIELD` | *Field declaration (includes enum constants)* | 필드 | `@NotNull`, `@Column` |
| `METHOD` | *Method declaration* | 메서드 | `@GetMapping`, `@Transactional` |
| `PARAMETER` | *Formal parameter declaration* | 파라미터 | `@RequestParam`, `@PathVariable` |
| `CONSTRUCTOR` | *Constructor declaration* | 생성자 | `@Autowired` |
| `LOCAL_VARIABLE` | *Local variable declaration* | 지역 변수 | 거의 안 씀 |
| `ANNOTATION_TYPE` | *Annotation type declaration* | 어노테이션 위의 어노테이션 | `@Retention`, `@Target` |
| `PACKAGE` | *Package declaration* | 패키지 | 거의 안 씀 |
| `TYPE_PARAMETER` | *Type parameter declaration* (1.8+) | 제네릭 타입 파라미터 | `<@NonNull T>` |
| `TYPE_USE` | *Use of a type* (1.8+) | 타입 사용 위치 | `List<@NonNull String>` |

```java
// 여러 곳에 붙일 수 있게 하려면 배열로
@Target({ElementType.METHOD, ElementType.TYPE})
public @interface MyAnnotation {}
```

---

## 3단계: 어노테이션을 읽는 원리 (리플렉션)

**모든 어노테이션 처리의 근본 원리는 리플렉션이다.**

```java
// 1. 커스텀 어노테이션 정의
@Retention(RetentionPolicy.RUNTIME)   // 실행 중에 읽을 수 있게
@Target(ElementType.FIELD)            // 필드에 붙일 수 있게
public @interface NotEmpty {}

// 2. 모델에 붙이기
public class User {
    @NotEmpty
    private String name;

    @NotEmpty
    private String email;
}

// 3. 리플렉션으로 읽어서 처리
public class MyValidator {
    public static void validate(Object obj) throws Exception {
        // 객체의 모든 필드를 순회
        for (Field field : obj.getClass().getDeclaredFields()) {
            // "이 필드에 @NotEmpty 스티커가 붙어있나?"
            if (field.isAnnotationPresent(NotEmpty.class)) {
                field.setAccessible(true);
                Object value = field.get(obj);
                if (value == null || value.toString().isEmpty()) {
                    throw new RuntimeException(field.getName() + "은 비어있을 수 없습니다");
                }
            }
        }
    }
}
```

**이게 전부다.** Spring이든 JPA든 Hibernate Validator든, 내부적으로 하는 일은 결국:

```
1. 리플렉션으로 클래스/필드/메서드 정보 꺼냄
2. 거기에 어노테이션 붙어있는지 확인
3. 붙어있으면 → 정해진 로직 실행
```

---

## 4단계: Spring에서 어노테이션이 처리되는 시점

HTTP 요청이 들어왔을 때, 어노테이션이 읽히는 순서:

```
클라이언트 요청 (HTTP)
│
▼
┌─────────────────────────────────────────┐
│ [1] Filter                              │
│  서블릿 레벨. Spring 밖에서 동작         │
│  예: @WebFilter                         │
│  용도: 인코딩, CORS, 로깅               │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [2] Interceptor (preHandle)             │
│  Spring MVC 레벨. 컨트롤러 진입 전       │
│  예: @RequireAuth (커스텀)              │
│  용도: 인증/인가, 권한 체크              │
│  → HandlerMethod에서 어노테이션 읽음     │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [3] AOP (Around/Before)                 │
│  메서드 호출을 프록시로 감싸서 처리       │
│  예: @Transactional, @Cacheable         │
│      @LogExecutionTime (커스텀)         │
│  용도: 트랜잭션, 캐싱, 로깅, 재시도      │
│  → 프록시 객체가 어노테이션 읽음         │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [4] Controller                          │
│  요청 매핑                              │
│  예: @GetMapping, @PostMapping          │
│      @RequestBody, @PathVariable        │
│  → DispatcherServlet이 어노테이션 읽음   │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [5] Argument Resolver & Validation      │
│  파라미터 바인딩 + 검증                  │
│  예: @Valid, @NotNull, @Size, @Email    │
│  → Hibernate Validator가 어노테이션 읽음 │
│  → 실패 시 MethodArgumentNotValidException │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [6] Service / Repository                │
│  비즈니스 로직 실행                      │
│  예: @Service, @Repository, @Autowired  │
│      @Transactional (여기서도 동작)      │
│  → Spring IoC 컨테이너가 읽음 (빈 등록)  │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│ [7] JPA / DB                            │
│  엔티티 매핑                             │
│  예: @Entity, @Table, @Column, @Id      │
│      @OneToMany, @ManyToOne             │
│  → Hibernate가 어노테이션 읽음           │
└─────────────────────────────────────────┘
```

---

## 주요 어노테이션 분류표

### 앱 시작 시 (Bean 등록 단계)

Spring이 뜰 때 컴포넌트 스캔으로 읽는다.

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@Component` | Spring IoC | 빈으로 등록 |
| `@Service` | Spring IoC | 빈으로 등록 (서비스 계층 표시) |
| `@Repository` | Spring IoC | 빈으로 등록 + DB 예외 변환 |
| `@Controller` | Spring MVC | 빈으로 등록 + 요청 매핑 대상 |
| `@Configuration` | Spring IoC | 설정 클래스로 등록 |
| `@Bean` | Spring IoC | 메서드 반환값을 빈으로 등록 |
| `@Autowired` | Spring IoC | 의존성 주입 |

### Filter & Interceptor (요청 전처리)

| 어노테이션 | 읽는 주체 | 하는 일 | 동작 위치 |
|-----------|----------|---------|----------|
| `@WebFilter` | 서블릿 컨테이너 (Tomcat) | 필터 등록 | Spring 밖 (서블릿 레벨) |
| `@Order` | Spring | 필터/빈 실행 순서 지정 | - |
| `@Component` (Filter 구현체에) | Spring IoC | Spring 관리 필터로 등록 | Spring 밖 (서블릿 레벨) |

> **Filter vs Interceptor 차이:**
> - **Filter**: Spring 밖, 서블릿 레벨. 모든 요청에 동작. Spring 빈 접근 어려움 (과거). 인코딩, CORS, 로깅용
> - **Interceptor**: Spring 안, MVC 레벨. 컨트롤러 메서드의 어노테이션을 읽을 수 있음. 인증/인가용

### 요청 매핑 (DispatcherServlet)

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@GetMapping` | DispatcherServlet | GET 요청 매핑 |
| `@PostMapping` | DispatcherServlet | POST 요청 매핑 |
| `@RequestBody` | HttpMessageConverter | JSON → 객체 변환 |
| `@ResponseBody` | HttpMessageConverter | 객체 → JSON 변환 |
| `@PathVariable` | ArgumentResolver | URL 경로 변수 바인딩 |
| `@RequestParam` | ArgumentResolver | 쿼리 파라미터 바인딩 |

### 검증 (Hibernate Validator)

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@Valid` | Spring MVC | 검증 트리거 |
| `@NotNull` | Hibernate Validator | null 불가 |
| `@NotEmpty` | Hibernate Validator | null, "" 불가 |
| `@Size(min, max)` | Hibernate Validator | 길이 제한 |
| `@Email` | Hibernate Validator | 이메일 형식 |
| `@Min`, `@Max` | Hibernate Validator | 숫자 범위 |

### AOP 기반 (프록시)

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@Transactional` | TransactionInterceptor | 트랜잭션 관리 |
| `@Cacheable` | CacheInterceptor | 결과 캐싱 |
| `@Async` | AsyncExecutionInterceptor | 비동기 실행 |
| `@Retryable` | RetryOperationsInterceptor | 재시도 |

### JPA (Hibernate)

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@Entity` | Hibernate | 엔티티 클래스 매핑 |
| `@Table` | Hibernate | 테이블명 지정 |
| `@Id` | Hibernate | PK 지정 |
| `@GeneratedValue` | Hibernate | PK 자동 생성 |
| `@Column` | Hibernate | 컬럼 매핑 |
| `@OneToMany` | Hibernate | 1:N 관계 |
| `@ManyToOne` | Hibernate | N:1 관계 |

### 컴파일 타임 (SOURCE)

| 어노테이션 | 읽는 주체 | 하는 일 |
|-----------|----------|---------|
| `@Override` | 컴파일러 | 오버라이딩 검증 |
| `@SuppressWarnings` | 컴파일러 | 경고 무시 |
| `@Getter/@Setter` | Lombok (컴파일러 플러그인) | 코드 자동 생성 |

---

## 커스텀 어노테이션 만드는 패턴

### 패턴 1: 리플렉션 직접 처리 (프레임워크 없이)

```java
// 정의
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface MaxLength {
    int value();
}

// 모델
public class Post {
    @MaxLength(100)
    private String title;
}

// 처리
for (Field field : obj.getClass().getDeclaredFields()) {
    MaxLength ann = field.getAnnotation(MaxLength.class);
    if (ann != null) {
        field.setAccessible(true);
        String value = (String) field.get(obj);
        if (value != null && value.length() > ann.value()) {
            throw new RuntimeException(field.getName() + "은 " + ann.value() + "자 이하");
        }
    }
}
```

### 패턴 2: AOP (Spring)

```java
// 정의
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface LogExecutionTime {}

// 처리 (Aspect)
@Aspect
@Component
public class LogAspect {
    @Around("@annotation(LogExecutionTime)")
    public Object log(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        System.out.println(joinPoint.getSignature() + ": "
            + (System.currentTimeMillis() - start) + "ms");
        return result;
    }
}

// 사용
@LogExecutionTime
public void heavyTask() { ... }
```

### 패턴 3: Interceptor (Spring MVC)

```java
// 정의
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface RequireRole {
    String value();
}

// 처리 (Interceptor)
@Component
public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res,
                             Object handler) {
        if (handler instanceof HandlerMethod method) {
            RequireRole ann = method.getMethodAnnotation(RequireRole.class);
            if (ann != null) {
                String userRole = getUserRole(req);
                if (!ann.value().equals(userRole)) {
                    res.setStatus(403);
                    return false;
                }
            }
        }
        return true;
    }
}

// 사용
@RequireRole("ADMIN")
@DeleteMapping("/users/{id}")
public void deleteUser(@PathVariable Long id) { ... }
```

---

## 한 줄 요약

> **어노테이션 = 스티커. 스티커 자체는 아무것도 안 한다. "누가, 언제 읽느냐"가 전부다.**
>
> - 컴파일러가 읽으면 → `@Override`
> - Spring IoC가 읽으면 → `@Component`, `@Autowired`
> - AOP 프록시가 읽으면 → `@Transactional`
> - Hibernate Validator가 읽으면 → `@NotNull`
> - Hibernate가 읽으면 → `@Entity`
> - 내가 리플렉션으로 읽으면 → 커스텀 처리
