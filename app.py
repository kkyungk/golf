from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import random
import threading
import requests
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

TARGET_URL = "https://www.welfare.mil.kr/content/content.do?m_code=82"
LOGIN_URL = "https://www.welfare.mil.kr/content/content.do?m_code=139&goCd=1&goUrl="
USERNAME = "rudrhks1"
PASSWORD = "kkyungk87!"
TELEGRAM_BOT_TOKEN = "7957216279:AAHJXw9VQevDalAIO_quHyHaekJUtnjPb80"
TELEGRAM_CHAT_ID = "1048697407"
TARGET_DATES = []
monitoring_thread = None
stop_event = threading.Event()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
    try:
        chromedriver_path = "./chromedriver.exe"  # Windows라면 "./chromedriver.exe"
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("ChromeDriver 성공적으로 초기화")
        return driver
    except Exception as e:
        logger.error(f"ChromeDriver 초기화 실패: {e}")
        logger.error(f"ChromeDriver 경로: {chromedriver_path}")
        raise

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
        logger.info(f"Telegram 메시지 전송: {message}")
    except Exception as e:
        logger.error(f"Telegram 전송 실패: {e}")

def auto_login(driver):
    logger.info(f"로그인 시도: {LOGIN_URL}")
    driver.get(LOGIN_URL)
    time.sleep(random.uniform(2, 4))
    try:
        driver.find_element("name", "cyber_id").send_keys(USERNAME)
        time.sleep(random.uniform(0.5, 1))
        driver.find_element("name", "cyber_pw").send_keys(PASSWORD)
        time.sleep(random.uniform(0.5, 1))
        driver.find_element("class name", "btnLogin").click()
        time.sleep(random.uniform(2, 5))
        logger.info("로그인 시도 완료")
        return "로그아웃" in driver.page_source
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        return False

def fetch_table_data(driver):
    logger.info("페이지 새로고침 및 데이터 가져오기 시작")
    driver.refresh()
    time.sleep(random.uniform(2, 4))
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    try:
        date_headers = [th.get_text(strip=True).split('(')[0].strip() for th in soup.find("thead").find_all("th")[1:]]
        table_data = {row.find("th").get_text(strip=True): [cell.get_text(strip=True) for cell in row.find_all("td")] for row in soup.find("tbody").find_all("tr")}
        logger.info(f"추출된 날짜: {date_headers}")
        return table_data, date_headers
    except Exception as e:
        logger.error(f"데이터 파싱 실패: {e}")
        raise

def monitor_updates():
    driver = setup_driver()
    if not auto_login(driver):
        send_telegram_message("⚠️ 로그인 실패로 모니터링 시작 불가")
        driver.quit()
        return
    
    driver.get(TARGET_URL)
    time.sleep(5)
    previous_data = {}
    notified_slots = set()
    
    send_telegram_message(f"⛳ 모니터링 시작\n관심 날짜: {', '.join(TARGET_DATES)}\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while not stop_event.is_set():
        try:
            data, date_headers = fetch_table_data(driver)
            notification_messages = []
            
            for course, values in data.items():
                prev_values = previous_data.get(course, [""] * len(values))
                for idx, (prev, curr) in enumerate(zip(prev_values, values)):
                    if idx >= len(date_headers) or date_headers[idx] not in TARGET_DATES:
                        continue
                    if prev != curr and curr.isdigit() and int(curr) > 0 and (not prev.isdigit() or int(prev) <= 0):
                        slot_id = f"{course}_{date_headers[idx]}"
                        if slot_id not in notified_slots:
                            message = f"🎯 <b>{course}</b> - <b>{date_headers[idx]}</b>에 잔여티 {curr}개 발생!"
                            notification_messages.append(message)
                            notified_slots.add(slot_id)
            
            if notification_messages:
                full_message = "🚨 잔여티 알림\n\n" + "\n\n".join(notification_messages) + f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_telegram_message(full_message)
            
            previous_data = data
        except Exception as e:
            logger.error(f"모니터링 중 오류: {e}")
        time.sleep(random.uniform(30, 60))
    
    send_telegram_message(f"⚠️ 모니터링 종료\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    driver.quit()

@app.route('/', methods=['GET', 'POST'])
def index():
    global TARGET_DATES, monitoring_thread
    logger.info(f"요청 수신: {request.method}")
    driver = setup_driver()
    try:
        if not auto_login(driver):
            logger.error("로그인 실패")
            return "로그인 실패", 500
        
        driver.get(TARGET_URL)
        time.sleep(5)
        data, date_headers = fetch_table_data(driver)
        
        if request.method == 'POST':
            TARGET_DATES = request.form.getlist('dates')
            logger.info(f"선택된 날짜: {TARGET_DATES}")
            if 'start' in request.form and not monitoring_thread:
                stop_event.clear()
                monitoring_thread = threading.Thread(target=monitor_updates)
                monitoring_thread.start()
                return jsonify({"status": "started"})
            elif 'stop' in request.form and monitoring_thread:
                stop_event.set()
                monitoring_thread.join()
                monitoring_thread = None
                return jsonify({"status": "stopped"})
        
        return render_template('index.html', dates=date_headers)
    except Exception as e:
        logger.error(f"서버 오류: {e}")
        return "서버 오류", 500
    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)