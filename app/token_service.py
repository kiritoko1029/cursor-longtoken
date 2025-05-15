import logging
import time
import uuid
import secrets
import hashlib
import base64
import requests
import os
import sys
from typing import Optional, Tuple, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import queue

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TokenService:
    def __init__(self):
        self._browser_queue = queue.Queue(maxsize=1)
        self._init_browser_pool()
        
    def _init_browser_pool(self):
        """初始化浏览器池（简单实现为单个浏览器实例）"""
        try:
            browser = self._create_browser_instance()
            self._browser_queue.put(browser)
            logging.info("浏览器池初始化完成")
        except Exception as e:
            logging.error(f"浏览器池初始化失败: {str(e)}")
    
    def _create_browser_instance(self):
        """创建一个新的浏览器实例"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-browser-side-navigation")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-default-apps")
            
            # 使用webdriver-manager自动下载和管理ChromeDriver
            try:
                logging.info("使用webdriver-manager安装ChromeDriver")
                service = Service(ChromeDriverManager().install())
                return webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e1:
                logging.warning(f"使用webdriver-manager安装ChromeDriver失败: {str(e1)}")
                
                # 尝试不同的ChromeDriver初始化方式
                try:
                    # 尝试直接初始化
                    logging.info("尝试直接初始化Chrome驱动")
                    return webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    logging.warning(f"直接初始化Chrome驱动失败: {str(e2)}")
                    
                    try:
                        # 尝试使用Service对象
                        logging.info("尝试使用Service对象创建Chrome驱动")
                        service = Service()
                        return webdriver.Chrome(service=service, options=chrome_options)
                    except Exception as e3:
                        logging.warning(f"使用Service创建Chrome驱动失败: {str(e3)}")
                        
                        # 如果是Windows系统，尝试使用指定路径
                        if sys.platform.startswith('win'):
                            try:
                                logging.info("尝试查找Chrome默认安装路径")
                                # Windows默认Chrome安装路径
                                chrome_paths = [
                                    os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
                                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                                ]
                                for chrome_path in chrome_paths:
                                    if os.path.exists(chrome_path):
                                        logging.info(f"找到Chrome: {chrome_path}")
                                        chrome_options.binary_location = chrome_path
                                        try:
                                            return webdriver.Chrome(options=chrome_options)
                                        except:
                                            continue
                            except Exception as e4:
                                logging.warning(f"指定Chrome路径创建驱动失败: {str(e4)}")
            
            # 所有方法都失败，返回模拟错误信息
            raise Exception("无法创建Chrome浏览器实例，请确保已安装Chrome浏览器")
        except Exception as e:
            logging.error(f"创建浏览器实例异常: {str(e)}")
            raise e
    
    def get_long_token(self, session_token: str, max_retries: int = 3) -> dict:
        """
        获取长效token
        
        Args:
            session_token: Cursor会话token
            max_retries: 最大重试次数
            
        Returns:
            dict: 包含userId, accessToken和错误信息的字典
        """
        browser = None
        try:
            # 检查浏览器池是否可用
            if self._browser_queue.empty():
                logging.warning("浏览器池为空，尝试重新初始化")
                self._init_browser_pool()
                
            # 从池中获取浏览器实例，设置超时以防阻塞
            try:
                browser = self._browser_queue.get(timeout=5)
                logging.info("成功从池中获取浏览器实例")
            except queue.Empty:
                logging.error("获取浏览器实例超时")
                return {
                    "success": False,
                    "userId": None,
                    "accessToken": None,
                    "error": "服务器繁忙，无法获取浏览器资源"
                }
            
            # 如果浏览器实例为None，返回错误
            if browser is None:
                logging.error("无效的浏览器实例")
                return {
                    "success": False,
                    "userId": None,
                    "accessToken": None,
                    "error": "浏览器初始化失败，请检查服务器配置"
                }
            
            # 设置cookies
            cookies = {
                "WorkosCursorSessionToken": session_token
            }
            
            # 获取token
            result = self._get_cursor_session_token(browser, cookies=cookies, max_attempts=max_retries)
            
            if result:
                userId, accessToken = result
                return {
                    "success": True,
                    "userId": userId,
                    "accessToken": accessToken,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "userId": None,
                    "accessToken": None,
                    "error": "无法获取token，请检查会话token是否有效"
                }
        except Exception as e:
            logging.error(f"获取长效token异常: {str(e)}")
            return {
                "success": False,
                "userId": None,
                "accessToken": None,
                "error": f"处理异常: {str(e)}"
            }
        finally:
            # 确保浏览器实例返回池中
            if browser:
                try:
                    # 重置浏览器状态
                    browser.delete_all_cookies()
                    self._browser_queue.put(browser)
                    logging.info("浏览器实例已归还至池中")
                except Exception as e:
                    logging.error(f"归还浏览器实例异常: {str(e)}")
                    # 如果出现异常，创建一个新的浏览器实例放回池中
                    try:
                        logging.info("尝试创建新的浏览器实例")
                        self._browser_queue.put(self._create_browser_instance())
                    except Exception as e2:
                        logging.error(f"无法创建新的浏览器实例: {str(e2)}")

    def _get_cursor_session_token(self, driver, max_attempts: int = 3, retry_interval: int = 2, cookies: Dict[str, str] = None) -> Optional[Tuple[str, str]]:
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
        
    def shutdown(self):
        """关闭所有浏览器资源"""
        try:
            # 尝试获取并关闭所有的浏览器实例
            logging.info("开始关闭浏览器资源")
            while not self._browser_queue.empty():
                browser = self._browser_queue.get_nowait()
                if browser:
                    try:
                        browser.quit()
                        logging.info("成功关闭浏览器实例")
                    except Exception as e:
                        logging.error(f"关闭浏览器实例出错: {str(e)}")
            logging.info("所有浏览器资源已关闭")
        except Exception as e:
            logging.error(f"关闭浏览器资源异常: {str(e)}")


# 创建token服务的单例实例
token_service = TokenService()
