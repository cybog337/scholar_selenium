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
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    all_articles = []
    
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # WebDriver 속성 숨기기
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        start_index = 0
        page_num = 1
        
        while True:
            url = f"https://scholar.google.com/scholar?q={SEARCH_QUERY}&hl=ko&as_sdt=0,5&as_ylo=2026&filter=0&start={start_index}"
            
            print(f"Page {page_num} 접속 중... (start={start_index})")
            print(f"URL: {url}")
            driver.get(url)
            time.sleep(5)
            
            # 디버깅: 페이지 제목 확인
            print(f"페이지 제목: {driver.title}")
            
            # 디버깅: 페이지 소스 일부 출력
            page_source = driver.page_source
            print(f"페이지 소스 길이: {len(page_source)} 글자")
            print(f"페이지 소스 시작 500자: {page_source[:500]}")
            
            # CAPTCHA 체크
            if "CAPTCHA" in page_source or "unusual traffic" in page_source:
                print("⚠️ Google이 봇을 감지했습니다 (CAPTCHA)")
                break
            
            # 스크린샷 저장 (디버깅용)
            try:
                screenshot_path = f'debug_page_{page_num}.png'
                driver.save_screenshot(screenshot_path)
                print(f"✅ 스크린샷 저장: {screenshot_path}")
            except Exception as e:
                print(f"스크린샷 저장 실패: {e}")
            
            try:
                # 방법 1: gs_ri 클래스
                results = driver.find_elements(By.CLASS_NAME, 'gs_ri')
                print(f"gs_ri 클래스로 찾은 결과: {len(results)}개")
                
                # 방법 2: CSS 선택자
                if not results:
                    results = driver.find_elements(By.CSS_SELECTOR, 'div.gs_r')
                    print(f"gs_r 클래스로 재시도: {len(results)}개")
                
                # 방법 3: XPath
                if not results:
                    results = driver.find_elements(By.XPATH, '//div[contains(@class, "gs_r")]')
                    print(f"XPath로 재시도: {len(results)}개")
                
                if not results:
                    print("❌ 더 이상 결과 없음 - 모든 선택자 실패")
                    # HTML 구조 확인
                    print("\n=== HTML 구조 샘플 (처음 1000자) ===")
                    print(page_source[:1000])
                    break
                
                print(f"✅ Page {page_num}: {len(results)}건 수집 시작")
                
                for idx, result in enumerate(results):
                    try:
                        # 제목
                        title_elem = result.find_element(By.CLASS_NAME, 'gs_rt')
                        title = title_elem.text.strip()
                        
                        # 링크
                        try:
                            link_elem = title_elem.find_element(By.TAG_NAME, 'a')
                            link = link_elem.get_attribute('href')
                        except:
                            link = "No Link"
                        
                        # 저자/저널 정보
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
                        
                        if idx == 0:
                            print(f"  첫 번째 논문: {title[:50]}...")
                    
                    except Exception as e:
                        print(f"  개별 결과 #{idx} 파싱 오류: {e}")
                        continue
                
                if len(results) < 10:
                    print("마지막 페이지 도달 (결과 10개 미만)")
                    break
                
                start_index += 10
                page_num += 1
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ 페이지 파싱 오류: {e}")
                import traceback
                traceback.print_exc()
                break
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ 브라우저 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n총 수집 건수: {len(all_articles)}건")
    
    unique_articles = []
    seen_links = set()
    for article in all_articles:
        if article["link"] not in seen_links and article["link"] != "No Link":
            unique_articles.append(article)
            seen_links.add(article["link"])
    
    if len(all_articles) != len(unique_articles):
        print(f"중복 제거: {len(all_articles) - len(unique_articles)}건")
    
    return unique_articles

def filter_new_articles(all_articles, sent_urls):
    """이미 발송한 논문 제외하고 신규만 필터링"""
    new_articles = []
    for article in all_articles:
        if article["link"] not in sent_urls:
            new_articles.append(article)
    return new_articles

def send_report(articles):
    """메일 발송"""
    msg = MIMEMultipart()
    msg['From'] = TARGET_EMAIL
    msg['To'] = TARGET_EMAIL
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    count = len(articles)
    msg['Subject'] = f"[Scholar-Selenium] {date_str} 신규 논문 알림 ({count}건)"
    
    if articles:
        body_parts = []
        for item in articles:
            part = f"[ {item['date']} ]\n{item['title']}\n{item['info']}\n{item['link']}"
            body_parts.append(part)
        
        body = "\n\n".join(body_parts)
    else:
        body = "신규 논문이 없습니다."
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(TARGET_EMAIL, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"메일 발송 완료: {count}건")
        return True
    except Exception as e:
        print(f"메일 발송 실패: {e}")
        return False

if __name__ == "__main__":
    if not GMAIL_PASSWORD:
        print("환경변수 설정 필요: GMAIL_PASSWORD")
        exit(1)
    
    sent_history = load_sent_history()
    print(f"기존 이력: {len(sent_history)}건")
    
    all_articles = fetch_scholar_data_selenium()
    print(f"검색 결과: {len(all_articles)}건")
    
    new_articles = filter_new_articles(all_articles, sent_history)
    print(f"신규 논문: {len(new_articles)}건")
    
    if send_report(new_articles):
        new_urls = [article["link"] for article in new_articles]
        save_sent_history(new_urls)
        print("이력 업데이트 완료")
