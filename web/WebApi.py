from flask import Flask, request, jsonify, send_file
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request,
    get_jwt
)
from werkzeug.utils import secure_filename
import os
from script.UserManageAPI import *
from datetime import timedelta
from util.YamlRead import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES_MINUTES

app = Flask(__name__)

# 配置 JWT
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
jwt = JWTManager(app)

def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_uid = get_jwt_identity()
        if not is_CheckAdmin(current_uid):
            return jsonify({"status": "error", "message": "需要管理员权限"}), 403
        return fn(*args, **kwargs)
    return wrapper

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    uid = request.json.get('uid')
    pwd = request.json.get('pwd')
    
    if not uid or not pwd:
        return jsonify({"status": "error", "message": "用户名密码的格式不正确"}), 400
    
    # 验证用户凭证
    user_info = GetUserInfo(uid)
    if not user_info:
        return jsonify({"status": "error", "message": "用户名或密码错误"}), 401
    
    authenticated = False
    authenticated = VerifyUserPassword(uid, pwd)
    
    if not authenticated:
        return jsonify({"status": "error", "message": "用户名或密码错误"}), 401
    
    # 创建JWT token
    additional_claims = {"is_admin": user_info.get('Admin', False)}
    access_token = create_access_token(
        identity=uid,
        additional_claims=additional_claims
    )
    
    return jsonify({
        "status": "success",
        "access_token": access_token,
        "user_info": {
            "uid": uid,
            "name": user_info.get('name'),
            "admin": user_info.get('Admin', False),
            "has_password": user_info.get('HasPassword', False)
        }
    })

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    uid = request.json.get('uid')
    password = request.json.get('password')
    email = request.json.get('email')
    
    if not uid or not password:
        return jsonify({"status": "error", "message": "用户名密码的格式不正确"}), 400
    
    create_result = CreateUserData(uid)
    if not create_result:
        return jsonify({"status": "error", "message": "用户已存在"}), 400
    if not RegisterUser(uid, password, email):
        return jsonify({"status": "error", "message": "密码设置失败"}), 500
    
    return jsonify({
        "status": "success",
        "uid": uid,
        "key": create_result[1]
    })

# 重置密码
@app.route('/api/user/<uid>/reset_password', methods=['PUT'])
@admin_required
def reset_password(uid):
    new_password = request.json.get('new_password')
    if not new_password:
        return jsonify({"status": "error", "message": "需要提供新密码"}), 400
    
    if not UpdateUserPassword(uid, new_password):
        return jsonify({"status": "error", "message": "密码重置失败"}), 500
    
    return jsonify({"status": "success"})

# 查询用户信息
@app.route('/api/user/<uid>', methods=['GET'])
@jwt_required()
def get_user_info(uid):
    current_uid = get_jwt_identity()
    if uid != current_uid and not get_jwt().get('is_admin'):
        return jsonify({"status": "error", "message": "无权访问该用户信息"}), 403
    
    info = GetUserInfo(uid)
    if not info:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 过滤敏感信息
    filtered_info = {
        "uid": info.get("uid"),
        "name": info.get("name"),
        "admin": info.get("Admin", False),
        "avatar": info.get("Avatar", False),
        "has_password": info.get("HasPassword", False)
    }
    
    return jsonify({"status": "success", "data": filtered_info})

# 授权管理员
@app.route('/api/op/<uid>', methods=['PUT'])
@admin_required
def grant_admin(uid):
    success = GiveOP(uid)
    if not success:
        return jsonify({"status": "error", "message": "授予管理员权限失败"}), 500
    return jsonify({"status": "success"})

# 重置密钥
@app.route('/api/user/<uid>/reset_key', methods=['PUT'])
@jwt_required()
def reset_key(uid):
    key = ReGetKey(uid)
    return jsonify({
        "status": "success",
        "data": {
            "uid": uid,
            "key": key
        }
    })

# 封禁用户
@app.route('/api/ban/<uid>', methods=['GET'])
@admin_required
def get_ban_info(uid):
    info = GetBanInfo(uid)
    return jsonify({"status": "success", "data": info})

# 修改昵称
@app.route('/api/user/<uid>/change_name', methods=['PUT'])
@jwt_required()
def change_name(uid):
    current_uid = get_jwt_identity()
    if uid != current_uid:
        return jsonify({"status": "error", "message": "修改昵称失败"}), 403
    
    new_name = request.json.get('name')
    if not new_name:
        return jsonify({"status": "error", "message": "昵称格式错误"}), 400
    
    success = ChangeName(uid, new_name)
    if not success:
        return jsonify({"status": "error", "message": "修改昵称失败"}), 500
    
    return jsonify({"status": "success"})