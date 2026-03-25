"""Sejong portal example: login + affiliation parsing + department list parsing.

Usage:
    export STUDENT_ID="2021xxxx"
    export PASSWORD="your-password"
    python examples/portal_department_parser.py
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) "
    "Gecko/20100101 Firefox/66.0"
)
TIMEOUT_SEC = 5


@dataclass
class StudentAffiliation:
    # 포털 상단 my_info 블록의 span.txt1
    name: str
    student_id: str
    level_label: str
    affiliation_raw: str
    division: str
    major: Optional[str]


class SejongPortalClient:
    """Minimal session client for portal pages."""

    def __init__(self, timeout_sec: int = TIMEOUT_SEC):
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def login(self, student_id: str, password: str) -> None:
        res = self.session.post(
            "https://portal.sejong.ac.kr/jsp/login/login_action.jsp",
            data={
                "mainLogin": "Y",
                "rtUrl": "blackboard.sejong.ac.kr",
                "id": student_id,
                "password": password,
            },
            headers={"Referer": "https://portal.sejong.ac.kr"},
            timeout=self.timeout_sec,
        )
        if res.status_code != 200:
            raise RuntimeError(f"Login failed with status={res.status_code}")
        if "ssotoken" not in res.headers.get("Set-Cookie", ""):
            raise RuntimeError("Login response does not include ssotoken.")

    def fetch_main_html(self) -> str:
        # legacy 코드에서 사용한 main.jsp를 그대로 사용
        res = self.session.get(
            "https://portal.sejong.ac.kr/main.jsp",
            timeout=self.timeout_sec,
        )
        if res.status_code != 200:
            raise RuntimeError(f"main.jsp fetch failed with status={res.status_code}")
        return res.text

    @staticmethod
    def parse_student_affiliation(html: str) -> StudentAffiliation:
        """Parse student id / affiliation from my-info block.

        Expected shape from your screenshot:
          span.txt1 -> name
          span.txt2 -> student id
          span.txt3 -> '학부' 같은 레이블
          span.txt4 -> '생명시스템학부 바이오융합공학전공' 같은 값
        """
        soup = BeautifulSoup(html, "html.parser")

        # 가장 구체적인 선택자부터 시도
        root = soup.select_one("div.top_myinfo div.text01")
        if root is None:
            root = soup

        # 이름은 span.txt1에 위치한다. 화면에 따라 따옴표가 포함될 수 있어 제거한다.
        name_el = root.select_one("span.txt1")
        sid = root.select_one("span.txt2")
        lvl = root.select_one("span.txt3")
        aff = root.select_one("span.txt4")
        if aff is None:
            raise RuntimeError("Cannot find affiliation element: span.txt4")

        name = name_el.get_text(" ", strip=True).strip('"').strip("'") if name_el else ""
        student_id = sid.get_text(strip=True) if sid else ""
        level_label = lvl.get_text(strip=True) if lvl else ""
        affiliation_raw = aff.get_text(" ", strip=True)
        division, major = split_division_and_major(affiliation_raw)
        #print(division, "++++",major)# 분리는 잘 되고 있는데 최종 적용할 때 잘 안되네
        return StudentAffiliation(
            name=name,
            student_id=student_id,
            level_label=level_label,
            affiliation_raw=affiliation_raw,
            division=division,
            major=major,
        )

    @staticmethod
    def parse_department_list(html: str) -> list[str]:
        """Extract department-like values from page HTML.

        Priority:
          1) <select> option text
          2) text nodes containing '학과' or '전공'
        """
        soup = BeautifulSoup(html, "html.parser")

        candidates = []
        for option in soup.select("select option"):
            text = option.get_text(" ", strip=True)
            if not text or text in {"선택", "전체", "All"}:
                continue
            candidates.append(text)

        if not candidates:
            text = soup.get_text("\n", strip=True)
            for line in text.splitlines():
                t = line.strip()
                if not t:
                    continue
                if ("학과" in t or "전공" in t) and len(t) <= 60:
                    candidates.append(t)

        # 순서 유지 중복 제거
        seen = set()
        result = []
        for item in candidates:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result


def split_division_and_major(affiliation_raw: str) -> tuple[str, Optional[str]]:
    """'학부 + 전공' 문자열을 분리한다.

    예:
      - '생명시스템학부 바이오융합공학전공' -> ('생명시스템학부', '바이오융합공학전공')
      - '컴퓨터공학과' -> ('컴퓨터공학과', None)

      -> 지금 분리한다고 되어있는데, 분리가 아니라 통째로 보내주는게 나을지도?? 일단 그렇게 요청을 했으니까...
      -> spring에서 전공이 none이면 학부로 저장, 전공이 있으면 전공으로 저장하는 방식
    """
    text = re.sub(r"\s+", " ", affiliation_raw).strip()
    if not text:
        return "", None

    m = re.match(r"^(.*?학부)\s+(.*)$", text)
    if m:
        division = m.group(1).strip()
        major = m.group(2).strip() or None
        return division, major

    return text, None


def main() -> None:
    student_id = os.getenv("STUDENT_ID")
    password = os.getenv("PASSWORD")
    #if not student_id or not password:
    #    raise RuntimeError("Set STUDENT_ID and PASSWORD environment variables first.")

    client = SejongPortalClient()
    client.login(student_id=student_id, password=password)
    html = client.fetch_main_html()

    my_info = client.parse_student_affiliation(html)
    
    result = {
        "studentNo": my_info.student_id or student_id,
        "passward": password,
        "name": my_info.name,
        "DetailDepartment": my_info.major  or my_info.affiliation_raw,
    }
    print(result)


if __name__ == "__main__":
    main()
