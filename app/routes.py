from flask import render_template, request, jsonify, redirect, url_for
import logging
from app import app
from app.token_service import token_service
import atexit

# 注册应用退出时的清理函数
atexit.register(token_service.shutdown)

@app.route('/')
def index():
    """主页，显示输入表单"""
    return render_template('index.html')

@app.route('/get-token', methods=['POST'])
def get_token():
    """处理获取token请求"""
    session_token = request.form.get('session_token')
    
    if not session_token:
        return render_template('result.html', success=False, error="请输入会话令牌")
    
    # 调用服务获取长效token
    result = token_service.get_long_token(session_token)
    
    # 根据结果渲染页面
    if result['success']:
        return render_template('result.html', 
                              success=True,
                              userId=result['userId'],
                              accessToken=result['accessToken'])
    else:
        return render_template('result.html',
                              success=False,
                              error=result['error'])

@app.route('/api', methods=['GET'])
def api_docs():
    """API文档页面"""
    return render_template('api.html')

@app.route('/api/token', methods=['POST'])
def api_token():
    """API端点，获取token并返回JSON"""
    # 检查内容类型
    if request.is_json:
        data = request.get_json()
        session_token = data.get('session_token')
    else:
        session_token = request.form.get('session_token')
    
    if not session_token:
        return jsonify({
            'success': False,
            'error': '缺少session_token参数'
        }), 400
    
    # 调用服务获取长效token
    result = token_service.get_long_token(session_token)
    
    # 返回API响应
    if result['success']:
        return jsonify({
            'success': True,
            'userId': result['userId'],
            'accessToken': result['accessToken']
        })
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400

@app.errorhandler(404)
def page_not_found(e):
    """404页面"""
    return render_template('index.html', error="页面不存在"), 404

@app.errorhandler(500)
def server_error(e):
    """500页面"""
    logging.exception("服务器内部错误")
    return render_template('index.html', error="服务器内部错误，请稍后重试"), 500
