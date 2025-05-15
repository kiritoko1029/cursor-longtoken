FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY . /app/

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
# 设置webdriver-manager的缓存目录和离线模式环境变量
ENV WDM_PROGRESS_BAR=0
ENV WDM_LOG_LEVEL=0
ENV WDM_SSL_VERIFY=0

# 安装Chrome浏览器和相关依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-symbola \
    fonts-noto \
    fonts-freefont-ttf \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 预下载ChromeDriver以便离线使用
RUN python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# 暴露端口
EXPOSE 5000

# 使用gunicorn启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "2", "run:app"]
