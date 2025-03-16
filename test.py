import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
import random

# URL 설정
TARGET_URL = "https://www.welfare.mil.kr/content/content.do?m_code=82"
LOGIN_URL = "https://www.welfare.mil.kr/content/content.do?m_code=139&goCd=1&goUrl="

# 로그인 정보
USERNAME = "rudrhks1"
PASSWORD = "kkyungk87!"

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = "7957216279:AAHJXw9VQevDalAIO_quHyHaekJUtnjPb80"  # 여기에 봇 토큰 입력
TELEGRAM_CHAT_ID = "1048697407"      # 여기에 채팅 ID 입력

# 관심 있는 날짜 설정 (예: 3/22, 3/23, 3/24)
TARGET_DATES = ["3/22", "3/23일", "3/24"]

def send_telegram_message(message):
    """
    텔레그램으로 메시지를 전송합니다.
    """
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("텔레그램 알림을 보내려면 봇 토큰을 설정해야 합니다.")
        return False
        
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID":
        print("텔레그램 알림을 보내려면 채팅 ID를 설정해야 합니다.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # HTML 형식의 메시지 지원
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"텔레그램 메시지 전송 성공: {message[:50]}...")
            return True
        else:
            print(f"텔레그램 메시지 전송 실패. 상태 코드: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"텔레그램 메시지 전송 중 오류 발생: {e}")
        return False

def auto_login(driver):
    """
    자동 로그인을 수행합니다.
    """
    driver.get(LOGIN_URL)
    time.sleep(random.uniform(2, 4))  # 랜덤 지연 시간 (2~4초)

    try:
        # 로그인 폼의 input 요소 선택
        username_input = driver.find_element(By.NAME, "cyber_id")
        password_input = driver.find_element(By.NAME, "cyber_pw")
    except Exception as e:
        print("로그인 입력 필드 찾기 실패:", e)
        return False
    
    actions = ActionChains(driver)
    actions.move_to_element(username_input).click().perform()
    time.sleep(random.uniform(0.5, 1.5))  # 클릭 후 대기

    for char in USERNAME:
        username_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))  # 글자당 랜덤 딜레이
    time.sleep(random.uniform(0.5, 1))

    actions.move_to_element(password_input).click().perform()
    time.sleep(random.uniform(0.5, 1.5))
    for char in PASSWORD:
        password_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))
    
    try:
        login_button = driver.find_element(By.CLASS_NAME, "btnLogin")
        actions.move_to_element(login_button).click().perform()
    except Exception as e:
        print("로그인 버튼 찾기 실패:", e)
        return False
    
    time.sleep(random.uniform(2, 5))  # 로그인 후 대기

    
    # 로그인 성공 여부 확인
    try:
        logout_element = driver.find_element(By.XPATH, "//a[contains(text(), '로그아웃')]")
        print("로그인 성공!")
        return True
    except:
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "error_message")
            print(f"로그인 오류: {error_msg.text}")
        except:
            print("로그인 상태를 확인할 수 없습니다.")
        return False

def fetch_table_data(driver):
    """
    대상 페이지에서 테이블 데이터를 파싱하여 골프장별 잔여티 정보와 날짜 정보를 반환합니다.
    """
    print("페이지 새로고침 중...")
    time.sleep(random.uniform(1, 3))  # 새로고침 전 랜덤 대기
    driver.refresh()  # 새로고침 실행
    time.sleep(random.uniform(2, 4))  # 새로고침 후 로딩 대기

    driver.get(TARGET_URL)
    time.sleep(random.uniform(2,4))  # 페이지 로딩 대기

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(random.uniform(1, 2))
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(1, 2))

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # 날짜 정보 추출
    date_headers = []
    thead = soup.find("thead")
    if thead:
        th_elements = thead.find_all("th")
        for th in th_elements[1:]:  # 첫 번째 th는 "시설명"이므로 제외
            date_text = th.get_text(strip=True).split('(')[0].strip()  # 예: "3/22(토)" -> "3/22"
            date_headers.append(date_text)
    
    if not date_headers:
        print("날짜 정보를 찾을 수 없습니다.")
    else:
        print("추출된 날짜 정보:", date_headers)
        # TARGET_DATES가 date_headers에 포함되어 있는지 확인
        missing_dates = [d for d in TARGET_DATES if d not in date_headers]
        if missing_dates:
            print(f"경고: 다음 관심 날짜가 테이블에 없습니다: {missing_dates}")
    
    # 테이블 데이터 추출
    tbody = soup.find("tbody")
    if not tbody:
        print("tbody를 찾을 수 없습니다. 페이지 구조 또는 로그인 상태를 확인하세요.")
        return None, None

    table_data = {}
    rows = tbody.find_all("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue
            
        course = cells[0].get_text(strip=True)
        values = []
        for cell in cells[1:]:  # 첫 번째 셀(th)을 제외하고 나머지 셀(td)만 처리
            # <a> 태그가 있으면 내부 텍스트, 없으면 셀 텍스트 추출
            a_tag = cell.find("a")
            text = a_tag.get_text(strip=True) if a_tag else cell.get_text(strip=True)
            values.append(text)
        table_data[course] = values
    
    # 디버깅용 출력 (관심 날짜만 필터링)
    print("\n파싱된 테이블 데이터 (관심 날짜만):")
    for course, values in table_data.items():
        print(f"{course}:")
        for i, value in enumerate(values):
            if i < len(date_headers) and date_headers[i] in TARGET_DATES:
                print(f"  {date_headers[i]}: {value}")
        
    return table_data, date_headers

def monitor_updates(driver):
    """
    페이지 데이터를 주기적으로 파싱하여 이전 데이터와 비교한 후,
    관심 있는 날짜에 잔여티가 예약 가능한 상태로 변경되면 텔레그램으로 알림을 전송합니다.
    """
    previous_data = {}
    date_headers = []
    notified_slots = set()
    
    print("잔여티 업데이트 모니터링 시작")
    print(f"현재 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"관심 날짜: {', '.join(TARGET_DATES)}")
    
    start_message = f"⛳ 골프장 잔여티 모니터링이 시작되었습니다.\n\n관심 날짜: {', '.join(TARGET_DATES)}\n\n시작 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram_message(start_message)
    
    try:
        while True:
            data, headers = fetch_table_data(driver)
            if headers:
                date_headers = headers
                
            if data is None:
                print("데이터를 가져오지 못했습니다. 로그인 상태나 페이지 구조를 확인하세요.")
            else:
                print(f"\n===== {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 업데이트 =====")
                
                notification_messages = []
                
                for course, values in data.items():
                    prev_values = previous_data.get(course, [""] * len(values))
                    for idx, (prev, curr) in enumerate(zip(prev_values, values)):
                        if idx >= len(date_headers):
                            continue
                            
                        date_info = date_headers[idx]
                        
                        # 관심 날짜에 대해서만 처리
                        if date_info not in TARGET_DATES:
                            continue
                            
                        # 값이 변경되었을 때 출력
                        if prev != curr:
                            print(f"{course} - {date_info}: {prev} → {curr}")
                            
                            # 예약 가능 상태로 변경된 경우 알림
                            if curr.isdigit() and int(curr) > 0 and (not prev.isdigit() or int(prev) <= 0):
                                slot_id = f"{course}_{date_info}"
                                if slot_id not in notified_slots:
                                    message = f"🎯 <b>{course}</b> - <b>{date_info}</b>에 잔여티 {curr}개 발생!"
                                    notification_messages.append(message)
                                    notified_slots.add(slot_id)
                
                if notification_messages:
                    full_message = "🚨 골프장 잔여티 알림 🚨\n\n" + "\n\n".join(notification_messages)
                    full_message += f"\n\n⏰ 업데이트 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_telegram_message(full_message)
                
                previous_data = data
                
            # 사람이 새로고침하는 것처럼 랜덤 대기 (300~900초)
            wait_time = random.uniform(300, 900)
            print(f"\n다음 업데이트까지 {wait_time:.1f}초 대기 중...")
            time.sleep(wait_time)
    except KeyboardInterrupt:
        print("모니터링을 중단합니다.")
        end_message = f"⚠️ 골프장 잔여티 모니터링이 중단되었습니다.\n\n종료 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_telegram_message(end_message)

def main():
    chrome_options = Options()
    # headless 모드 비활성화 (사람처럼 보이게 창 표시)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 자동화 탐지 비활성화
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    # 창 크기 설정 (사람이 브라우저를 열 때처럼)
    driver.set_window_size(1280, 720)

    print("=========================================")
    print("군인공제회 골프장 잔여티 모니터링 프로그램")
    print("=========================================")
    print("텔레그램 알림 설정이 필요합니다.")
    print("=========================================")
    
    # 텔레그램 설정 확인
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID":
        print("경고: 텔레그램 봇 토큰과 채팅 ID를 설정해야 알림을 받을 수 있습니다.")
        print("스크립트 상단의 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 설정하세요.")
        user_input = input("설정 없이 계속하시겠습니까? (y/n): ")
        if user_input.lower() != 'y':
            print("프로그램을 종료합니다.")
            return
        
    try:
        print("로그인 시도 중...")
        login_success = auto_login(driver)
        
        if login_success:
            print(f"잔여티 예약 사이트({TARGET_URL})로 이동합니다...")
            driver.get(TARGET_URL)
            time.sleep(5)  # 페이지 로딩 대기
            
            # 날짜 정보 추출
            data, date_headers = fetch_table_data(driver)
            if not date_headers:
                print("날짜 정보를 가져올 수 없습니다. 프로그램을 종료합니다.")
                return
            
            # 추출된 날짜 출력
            print("\n추출된 날짜 정보:")
            for i, date in enumerate(date_headers, 1):
                print(f"{i}. {date}")
            
            # 사용자에게 날짜 선택 요청
            print("\n모니터링하고 싶은 날짜 번호를 입력하세요 (예: 1, 2 또는 1 2). 여러 날짜는 띄어쓰기로 구분:")
            while True:
                try:
                    user_input = input("> ").strip()
                    selected_indices = [int(i) - 1 for i in user_input.split()]
                    if all(0 <= i < len(date_headers) for i in selected_indices):
                        global TARGET_DATES
                        TARGET_DATES = [date_headers[i] for i in selected_indices]
                        print(f"선택된 날짜: {', '.join(TARGET_DATES)}")
                        break
                    else:
                        print("잘못된 번호입니다. 범위 내의 번호를 입력하세요.")
                except ValueError:
                    print("숫자를 입력하세요. 예: 1 2")
            
            # 모니터링 시작
            monitor_updates(driver)
        else:
            print("자동 로그인에 실패했습니다.")
            end_message = "⚠️ 골프장 잔여티 모니터링을 시작할 수 없습니다. 로그인에 실패했습니다."
            send_telegram_message(end_message)
    except Exception as e:
        print(f"메인 함수에서 오류 발생: {e}")
        error_message = f"❌ 골프장 잔여티 모니터링 중 오류가 발생했습니다.\n\n오류: {str(e)}"
        send_telegram_message(error_message)
    finally:
        # driver.quit()  # 디버깅 중이라면 주석 처리
        pass

if __name__ == "__main__":
    main()