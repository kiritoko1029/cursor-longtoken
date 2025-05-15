# Cursor 长效Token获取

一个用于获取Cursor长效访问令牌的Web服务。用户只需提供会话token，即可获取长期有效的访问令牌。

## 功能特点

- 通过Web界面或API获取长效Token
- 基于Selenium自动化，无需手动操作
- 支持Docker容器化部署
- 美观现代的UI界面（基于Tailwind CSS）
- 提供多种格式（JSON、TXT、.env）的Token下载功能
- 提供清晰的使用说明

## 环境要求

- Docker 和 Docker Compose（推荐，用于容器化部署）
- 或者 Python 3.8+ 环境和Chrome浏览器（本地开发）

## 快速开始

### 使用Docker部署（推荐）

1. 克隆仓库：

```bash
git clone https://github.com/kiritoko1029/cursor-longtoken.git
cd cursor-longtoken
```

2. 构建并启动容器：

```bash
docker-compose up -d
```

3. 访问服务：

打开浏览器，访问 http://localhost:5000

### 本地开发环境

1. 克隆仓库：

```bash
git clone https://github.com/kiritoko1029/cursor-longtoken.git
cd cursor-longtoken
```

2. 创建虚拟环境并安装依赖：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. 确保已安装Chrome浏览器

4. 启动服务：

```bash
python run.py
```

5. 访问服务：

打开浏览器，访问 http://localhost:5000

## 使用方法

### Web界面使用

1. 在Cursor应用中使用开发者工具，查找Cookie中的`WorkosCursorSessionToken`值
2. 将该值输入到网站的表单中，点击提交
3. 获取长效Token和用户ID
4. 可以选择复制Token或以不同格式下载（JSON、TXT、.env）

### API使用

**请求示例：**

```http
POST /api/token
Content-Type: application/json

{
    "session_token": "your_session_token"
}
```

**响应示例：**

```json
{
    "success": true,
    "userId": "user_123456",
    "accessToken": "eyJhbGci..."
}
```

## 技术架构

- **后端**: Flask (Python)
- **前端**: Tailwind CSS + JavaScript
- **容器化**: Docker + Docker Compose
- **自动化**: Selenium WebDriver
- **浏览器管理**: webdriver-manager

## 注意事项

- 本工具仅用于学习研究，请勿用于非法用途
- 请妥善保管获取到的Token，避免泄露
- 服务启动可能需要一些时间，因为需要初始化Chrome浏览器

## 许可协议

MIT

## 免责声明

此工具仅用于教育和研究目的。使用者应当遵守相关法律法规和服务条款。作者不对任何滥用行为负责。
