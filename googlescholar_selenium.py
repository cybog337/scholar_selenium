import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from datetime import datetime
import time

# ================= 사용자 설정 =================
TARGET_EMAIL = "cybog337@gmail.com"
SEARCH_QUERY = "biogems -biogem -cjter"
HISTORY_FILE = "sent_list_scholar.txt"

GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
# =============================================

def load_sent_history():
    """이전에 발송한 URL 목록 로드"""
    if not os.path.exists(HISTORY_FILE):
        return set()
    
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_sent_history(urls):
    """새로 발송한 URL을 이력 파일에 추가"""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')

def extract_date_info(text):
    """날짜 정보 추출"""
    match = re.search(r'(202[0-9])\s*-?\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?', text)
    if match:
        year = match.group(1)
        month = match.group(2) if match.group(2) else ""
        return f"{year} {month}".strip()
    return "2026"

def fetch_scholar_data_selenium():
    """Selenium으로 Google Scholar 전체 수집"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    all_articles = []
    
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        start_index = 0
        page_num = 1
        
        while True:
            url = f"https://scholar.google.com/scholar?q={SEARCH_QUERY}&hl=ko&as_sdt=0,5&as_ylo=2026&filter=0&start={start_index}"
            
            print(f"Page {page_num} 접속 중... (start={start_index})")
            driver.get(url)
            
            time.sleep(3)
            
            try:
                results = driver.find_elements(By.CLASS_NAME, 'gs_ri')
                
                if not results:
                    print("더 이상 결과 없음")
                    break
                
                print(f"Page {page_num}: {len(results)}건 수집")
                
                for result in results:
                    try:
                        title_elem = result.find_element(By.CLASS_NAME, 'gs_rt')
                        title = title_elem.text.strip()
                        
                        try:
                            link_elem = title_elem.find_element(By.TAG_NAME, 'a')
                            link = link_elem.get_attribute('href')
                        except:
                            link = "No Link"
                        
                        try:
                            info_elem = result.find_element(By.CLASS_NAME, 'gs_a')
                            info = info_elem.text.strip()
                        except:
                            info = "정보 없음"
                        
                        date_str = extract_date_info(info)
                        
                        all_articles.append({
                            "title": title,
                            "link": link,
                            "info": info,
                            "date": date_str
                        })
                    
                    except Exception as e:
                        print(f"개별 결과 파싱 오류: {e}")
                        continue
                
                if len(results) < 10:
                    print("마지막 페이지 도달")
                    break
                
                start_index += 10
                page_num += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"페이지 파싱 오류: {e}")
                break
        
        driver.qu
