from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

# 대상 페이지 및 로그인 URL (실제 URL 확인 필요)
TARGET_URL = "https://www.welfare.mil.kr/content/content.do?m_code=82"
LOGIN_URL = "https://www.welfare.mil.kr/content/content.do?m_code=139&goCd=1&goUrl="  # 예시 URL

def auto_login(driver, username, password):
    """
    Selenium을 사용해 로그인 페이지에 접속, 아이디와 비밀번호 입력 후 자동 로그인.
    실제 input의 name 속성이나 로그인 버튼의 선택자는 사이트에 따라 달라질 수 있습니다.
    """
    driver.get(LOGIN_URL)
    time.sleep(2)  # 페이지 로딩 대기
    
    try:
        # 로그인 폼의 input 요소 선택 (이름은 실제 사이트에 맞게 수정)
        username_input = driver.find_element(cyber_id, "rudrhks1")
        password_input = driver.find_element(cyber_pw, "kkyungk87!")
    except Exception as e:
        print("로그인 입력 필드 찾기 실패:", e)
        return False
    
    # 입력값 설정
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)
    
    try:
        # 로그인 버튼 클릭 (버튼의 XPath 또는 CSS 선택자는 실제 사이트에 맞게 수정)
        login_button = driver.find_element(btnLogin, "//button[@type='submit']")
    except Exception as e:
        print("로그인 버튼 찾기 실패:", e)
        return False

    login_button.click()
    time.sleep(3)  # 로그인 처리 시간 대기

    # 로그인 성공 여부를 간단히 체크 (예: 로그인 페이지의 텍스트가 남아있지 않은지 확인)
    if "로그인" in driver.page_source:
        print("로그인 실패")
        return False
    else:
        print("로그인 성공")
        return True

def fetch_table_data(driver):
    """
    로그인된 세션을 유지한 상태에서 대상 페이지의 HTML을 가져와,
    BeautifulSoup을 이용해 테이블 데이터를 파싱합니다.
    """
    driver.get(TARGET_URL)
    time.sleep(3)  # 페이지 로딩 대기
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    tbody = soup.find("tbody")
    if not tbody:
        print("tbody를 찾을 수 없습니다. 페이지 구조 변경 또는 로그인 문제일 수 있습니다.")
        return None
    
    table_data = {}
    rows = tbody.find_all("tr")
    for row in rows:
        course = row.find("th").get_text(strip=True)
        cells = row.find_all("td")
        values = []
        for cell in cells:
            # <a> 태그가 있으면 내부 텍스트, 없으면 셀의 텍스트 추출
            a_tag = cell.find("a")
            text = a_tag.get_text(strip=True) if a_tag else cell.get_text(strip=True)
            values.append(text)
        table_data[course] = values
    return table_data

def is_available(text):
    """
    텍스트가 숫자이며 0보다 큰 경우 예약 가능한 상태로 판단.
    """
    if text.isdigit():
        return int(text) > 0
    return False

def monitor_updates(driver):
    """
    주기적으로 페이지 데이터를 파싱하여 이전 데이터와 비교 후,
    잔여티가 예약 가능한 상태로 변경되었을 때 알림 메시지(콘솔 출력)를 발생시킵니다.
    """
    previous_data = {}
    print("잔여티 업데이트 모니터링 시작")
    while True:
        data = fetch_table_data(driver)
        if data is None:
            print("데이터를 가져오지 못했습니다. 로그인 상태나 페이지 구조를 확인하세요.")
        else:
            for course, values in data.items():
                prev_values = previous_data.get(course, [""] * len(values))
                for idx, (prev, curr) in enumerate(zip(prev_values, values)):
                    # 값이 변경되고, 새 값이 예약 가능한 상태(숫자 > 0)인 경우
                    if prev != curr and curr.isdigit() and int(curr) > 0:
                        slot_num = idx + 1  # 인덱스 0부터 시작하므로 +1
                        print(f"[알림] {course}의 {slot_num}번째 슬롯 변경: {prev} -> {curr}")
                        # 추가: Telegram API 호출 등 알림 전송 기능 구현 가능
            previous_data = data
        time.sleep(30)  # 30초 간격으로 업데이트 확인

if __name__ == "__main__":
    chrome_options = Options()
    # headless 모드는 UI 확인이 어려울 수 있으니 테스트 후 필요 시 활성화하세요.
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        # 사용자로부터 로그인 정보 입력
        username = input("아이디를 입력하세요: ")
        password = input("비밀번호를 입력하세요: ")
        
        if auto_login(driver, username, password):
            monitor_updates(driver)
        else:
            print("자동 로그인에 실패했습니다.")
    finally:
        driver.quit()
