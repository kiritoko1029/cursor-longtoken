import logging
import time
import uuid
import secrets
import hashlib
import base64
import requests
from typing import Optional, Tuple, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_cursor_session_token(driver, max_attempts: int = 3, retry_interval: int = 2, cookies: Dict[str, str] = None) -> Optional[Tuple[str, str]]:
    """
    获取Cursor会话token
    
    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数
        retry_interval: 重试间隔(秒)
        cookies: 要设置的cookies字典，格式为{name: value}
        
    Returns:
        Tuple[str, str] | None: 成功返回(userId, accessToken)元组，失败返回None
    """
    logging.info("开始获取会话令牌")
    
    # 首先尝试使用UUID深度登录方式
    logging.info("尝试使用深度登录方式获取token")
    
    def _generate_pkce_pair():
        """生成PKCE验证对"""
        code_verifier = secrets.token_urlsafe(43)
        code_challenge_digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_digest).decode('utf-8').rstrip('=')    
        return code_verifier, code_challenge
    
    attempts = 0
    while attempts < max_attempts:
        try:
            verifier, challenge = _generate_pkce_pair()
            id = uuid.uuid4()
            client_login_url = f"https://www.cursor.com/cn/loginDeepControl?challenge={challenge}&uuid={id}&mode=login"
            
            # 先访问网站，以便可以设置cookie
            logging.info(f"首先访问网站: https://www.cursor.com/")
            driver.get("https://www.cursor.com/")
            time.sleep(1)
            
            # 如果提供了cookies，先设置到浏览器
            if cookies:
                logging.info("设置浏览器cookies")
                for name, value in cookies.items():
                    # 不指定domain，让浏览器自动匹配当前域名
                    driver.add_cookie({"name": name, "value": value, "path": "/"})
                logging.info("cookies设置完成")
            
            logging.info(f"访问深度登录URL: {client_login_url}")
            driver.get(client_login_url)
            
            # 使用WebDriverWait等待元素出现，最多等待5秒
            try:
                login_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Yes, Log In')]"))
                )
                logging.info("点击确认登录按钮")
                login_button.click()
                time.sleep(1.5)
                
                auth_poll_url = f"https://api2.cursor.sh/auth/poll?uuid={id}&verifier={verifier}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Cursor/0.48.6 Chrome/132.0.6834.210 Electron/34.3.4 Safari/537.36",
                    "Accept": "*/*"
                }
                
                logging.info(f"轮询认证状态: {auth_poll_url}")
                response = requests.get(auth_poll_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    accessToken = data.get("accessToken", None)
                    authId = data.get("authId", "")
                    
                    if accessToken:
                        userId = ""
                        if len(authId.split("|")) > 1:
                            userId = authId.split("|")[1]
                        
                        logging.info("成功获取账号token和userId")
                        return userId, accessToken
                else:
                    logging.error(f"API请求失败，状态码: {response.status_code}")
            except Exception as e:
                logging.warning(f"未找到登录确认按钮或点击失败: {str(e)}")
                
            attempts += 1
            if attempts < max_attempts:
                wait_time = retry_interval * attempts  # 逐步增加等待时间
                logging.warning(f"第 {attempts} 次尝试未获取到token，{wait_time}秒后重试...")
                time.sleep(wait_time)
                
        except Exception as e:
            logging.error(f"深度登录获取token失败: {str(e)}")
            attempts += 1
            if attempts < max_attempts:
                wait_time = retry_interval * attempts
                logging.warning(f"将在 {wait_time} 秒后重试...")
                time.sleep(wait_time)
    
    logging.error(f"在 {max_attempts} 次尝试后仍未获取到token")
    return None

def init_browser(headless: bool = False):
    """
    初始化浏览器
    
    Args:
        headless: 是否使用无头模式
        
    Returns:
        WebDriver: 初始化好的WebDriver对象
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    # if headless:
    chrome_options.add_argument("--headless")
    
    # 可选：添加其他常用选项
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 创建并返回WebDriver
    logging.info("初始化Chrome浏览器" + (" (无头模式)" if headless else ""))
    return webdriver.Chrome(options=chrome_options)

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 设置WorkosCursorSessionToken的值
    session_token = "user_0xxxxxx%3A%3Aeyxxxxxx"
    
    # 初始化浏览器
    driver = init_browser(headless=False)
    
    try:
        # 设置cookies
        cookies = {
            "WorkosCursorSessionToken": session_token
        }
        
        # 获取token
        result = get_cursor_session_token(driver, cookies=cookies)
        if result:
            userId, accessToken = result
            print(f"登录成功! userId: {userId}")
            print(f"accessToken: {accessToken}")
        else:
            print("登录失败")
    finally:
        driver.quit()