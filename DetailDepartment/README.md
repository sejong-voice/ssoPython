# DetailDepartment

###세종 포털에서 사용자 소속 문자열을 가져와 `DetailDepartment` 값을 만드는 모듈입니다.

###직접 만든 로직이고, 집현캠 로그인 이후 학번, 이름, 전공 등의 정보를 긁어오는 크롤링 모듈임

## 구성 파일

- `portal_department_parser.py`
  - 포털 로그인
  - `main.jsp` HTML 조회
  - 이름/학번/소속 파싱
  - `split_division_and_major()`로 `학부/전공` 분리
- `portal_profile_router.py`
  - FastAPI 엔드포인트 `/auth/detail-department`
  - 파싱 결과를 API 응답으로 반환

## 현재 동작

`portal_profile_router.py`의 응답은 아래 로직을 사용합니다.

```python
"DetailDepartment": info.major or info.affiliation_raw
```

즉,

- `major`가 있으면 `major` 반환
- 없으면 원문 소속 문자열(`affiliation_raw`) 반환

## 파싱 규칙

`split_division_and_major(affiliation_raw)` 기준:

- 입력: `생명시스템학부 바이오융합공학전공`
  - 출력: `division='생명시스템학부'`, `major='바이오융합공학전공'`
- 입력: `컴퓨터공학과`
  - 출력: `division='컴퓨터공학과'`, `major=None`

## 예시 결과

현재 응답 로직(`info.major or info.affiliation_raw`) 기준:

- `컴퓨터공학과` -> `컴퓨터공학과`
- `생명시스템학부 바이오융합공학전공` -> `바이오융합공학전공`

## API 사용

### 요청

- Method: `POST`
- Path: `/auth/detail-department`
- Body:

```json
{
  "student_id": "2021xxxx",
  "password": "your-password"
}
```

### 응답 예시

```json
{
  "student_id": "2021xxxx",
  "password": "your-password",
  "name": "홍길동",
  "DetailDepartment": "바이오융합공학전공"
}
```

## 로컬 실행

### 1) API 서버 실행

```bash
python /Users/cheonjuhwan/Documents/GitHub/ssoPython/app/main.py
```

### 2) 파서 단독 테스트

```bash
export STUDENT_ID="2021xxxx"
export PASSWORD="your-password"
python /Users/cheonjuhwan/Documents/GitHub/ssoPython/DetailDepartment/portal_department_parser.py
```

## 자주 헷갈리는 포인트

- `main()` 안의 `print()`는 **파일 직접 실행 시에만** 보입니다.
- FastAPI 호출 시 로그를 보려면 `portal_profile_router.py` 내부에 `print()`를 넣어야 합니다.

## 응답 정책 바꾸는 위치

- API 반환값 정책 변경:
  - `DetailDepartment/portal_profile_router.py`
  - `"DetailDepartment": ...` 한 줄 수정
- 분리 규칙 변경:
  - `DetailDepartment/portal_department_parser.py`
  - `split_division_and_major()` 수정
