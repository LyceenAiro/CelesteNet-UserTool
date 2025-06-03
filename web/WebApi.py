from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt
)
import os
from functools import wraps
from script.UserManageAPI import (sql,
    BanUser, ChangeName, CreateUserData, DeBan,
    DeOP, GetBanInfo, GetUserInfo, GiveOP,
    InsertAvatar, ReGetKey, RemoveUser,
    is_CheckAdmin, is_CheckSuperAdmin
)
from script.NetApiFormat import *
from datetime import timedelta
from script.WebUserManage import UpdateUserPassword, VerifyUserPassword
from util.YamlRead import (
    CelesteNetWebRedirect, 
    UserDataPath, WebTitle,
    JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES_MINUTES
)

app = Flask(__name__, template_folder='html')

# 配置 JWT
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
jwt = JWTManager(app)

@app.route('/')
def index():
    return render_template('index.html')

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_uid = get_jwt_identity()
        if not is_CheckAdmin(current_uid):
            return jsonify({"status": "error", "message": "需要管理员权限"}), 403
        return fn(*args, **kwargs)
    return wrapper

def super_admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_uid = get_jwt_identity()
        if not is_CheckSuperAdmin(current_uid) or not is_CheckAdmin(current_uid):
            return jsonify({"status": "error", "message": "需要超级管理员权限"}), 403
        return fn(*args, **kwargs)
    return wrapper

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    """
    输入类型:
    uid         用户名
    pwd         密码

    网页用户登录接口
    """
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

# 退出登录
@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"status": "success"})

# 前端重定向API
@app.route('/api/websetting', methods=['GET'])
def WebSetting():
    return jsonify({
            "celestenet_url": f"http://{CelesteNetWebRedirect}",
            "webtitle": WebTitle
        })

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    """
    输入类型:
    uid         注册用户名
    new_pwd     新的密码

    用户可以注册自己的网页账户
    注册完成后会自动创建客户端相关的用户信息

    返回字段:
    status      注册是否成功
    message     注册失败后返回的信息
    uid         注册成功返回uid
    key         注册成功后返回key
    """
    uid = request.json.get('uid')
    password = request.json.get('password')
    email = request.json.get('email')
    
    if not uid or not password:
        return jsonify({"status": "error", "message": "用户名密码的格式不正确"}), 400
    create_result = CreateUserData(uid, password, email)
    if not create_result:
        return jsonify({"status": "error", "message": "用户已存在"}), 400    
    return jsonify({
        "status": "success",
        "uid": uid,
        "key": create_result[1]
    })

# 重置密码
@app.route('/api/user/<uid>/reset_password', methods=['PUT'])
@jwt_required()
def reset_password(uid):
    """
    输入类型:
    <uid>       在链接中插入: 用户名
    new_pwd     新的密码

    用户可以修改自己的密码

    返回字段:
    success     修改成功
    error       修改失败
    message     修改失败原因, 只有在修改失败后携带
    """
    new_password = request.json.get('new_pwd')
    current_uid = get_jwt_identity()
    if uid != current_uid and not get_jwt().get('is_admin'):
        return jsonify({"status": "error", "message": "无权修改该用户的密码"}), 403
    if not new_password:
        return jsonify({"status": "error", "message": "需要提供新密码"}), 400
    if not UpdateUserPassword(uid, new_password):
        return jsonify({"status": "error", "message": "密码重置失败"}), 500
    return jsonify({"status": "success"})

# 查询用户信息
@app.route('/api/user/<uid>', methods=['GET'])
@jwt_required()
def get_user_info(uid):
    """
    输入类型:
    <uid>       在链接中插入: 用户名

    用户在登录后可以获取到自己的用户信息
    如果GetUserInfo不为None, 则返回以下格式
    {
        "uid": None,
        "key": None,
        "name": None,
        "Avatar": False,
        "Admin": False,
        "Email": None
    }

    返回字段:
    uid         用户名
    key         密钥
    name        昵称
    Avatar      是否有头像
    Admin       是否是管理员
    Email       邮箱地址, 可以是None
    """
    current_uid = get_jwt_identity()
    if uid != current_uid and not get_jwt().get('is_admin'):
        return jsonify({"status": "error", "message": "无权访问该用户信息"}), 403
    info = GetUserInfo(uid)
    if not info:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    return jsonify({"status": "success", "data": info})

# 授权管理员
@app.route('/api/op', methods=['GET'])
@super_admin_required
def grant_admin():
    """
    输入类型:
    uid         想要授权管理员的用户

    授权一个用户为管理员, 这个行为在网页中是热生效的, 但是在客户端中需要重新登录
    GiveOP只会返回bool类型, 用于判断是否成功授权管理员

    返回字段:
    success     授权成功
    error       授权失败
    message     授权失败原因, 只有在授权失败后携带
    """
    uid = request.args.get('uid')
    success = GiveOP(uid)
    if not success:
        return jsonify({"status": "error", "message": "授予管理员权限失败"}), 500
    return jsonify({"status": "success"})

# 移除管理员
@app.route('/api/deop', methods=['GET'])
@super_admin_required
def remove_admin():
    """
    输入类型:
    uid         想要移除管理员的用户

    将管理员用户移除管理员

    返回字段:
    success     移除成功
    error       移除失败
    message     移除失败原因, 只有在移除失败后携带
    """
    uid = request.args.get('uid')
    success = DeOP(uid)
    if not success:
        return jsonify({"status": "error", "message": "回收管理员权限失败"}), 500
    return jsonify({"status": "success"})

# 重置密钥
@app.route('/api/user/<uid>/reset_key', methods=['PUT'])
@jwt_required()
def reset_key(uid):
    """
    输入类型:
    uid         想要授权管理员的用户
    
    密钥是从客户端登录CelesteNet的唯一途径
    用户在登录网站后可以自己通过重置密钥功能自行重置密钥
    在重置完毕后会返回最新的uid和key

    返回字段:
    uid         用户名
    key         重置后的最新密钥
    """
    current_uid = get_jwt_identity()
    if uid == current_uid:
        key = ReGetKey(current_uid)
    return jsonify({
        "status": "success",
        "data": {
            "uid": current_uid,
            "key": key
        }
    })

# 封禁用户
@app.route('/api/ban', methods=['GET'])
@admin_required
def ban_user():
    """
    输入类型:
    uid         想要封禁的用户
    minutes     封禁分钟数
    days        封禁天数
    reason      封禁原因 (可选)

    如果BanUser为空则返回False, 最后输出的data自动转换为None
    如果BanUser不为空则返回下面格式
    {
        "UID": Example1,
        "Name": Example_Test1,
        "Reason": "封禁例子",
        "From": "2025-05-01 12:00:00",
        "To": "2025-05-01 08:30:00"
    }

    返回字段:
    UID         用户名
    Name        用户昵称
    Reason      封禁内容(封禁原因)
    From        开始封禁时间
    To          结束封禁时间, 如果为None为永久封禁
    """
    uid = request.args.get('uid')
    try:
        if is_CheckAdmin(uid):
            return jsonify({"status": "error", "message": "管理员无法封禁"})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "没有搜索到该用户信息"})
    minutes = int(request.args.get('minutes', 0))
    days = int(request.args.get('days', 0))
    reason = request.args.get('reason', '')
    info = BanUser(uid, minutes, days, reason)
    if not info:
        info = None
    return jsonify({"status": "success", "data": info})

# 解禁用户
@app.route('/api/deban', methods=['GET'])
@super_admin_required
def deban_user():
    """
    输入类型:
    uid        想要封禁的用户

    尝试删除一名用户的封禁记录
    DeBan只会返回bool类型

    返回字段:
    True        如果删除成功
    False       删除失败
    """
    uid = request.args.get('uid')
    info = DeBan(uid)
    return jsonify({"status": "success", "data": info})

# 修改昵称
@app.route('/api/user/<uid>/change_name', methods=['PUT'])
@jwt_required()
def change_name(uid):
    """
    输入类型:
    <uid>       在链接中插入: 用户名
    name        想要修改成的新昵称

    用户在网页登录后可以自行修改昵称
    这只会影响在客户端登录后显示的昵称
        
    返回字段:
    success     修改成功
    error       修改失败
    message     修改失败原因, 只有在修改失败后携带
    """
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

# 注销用户
@app.route('/api/user/<uid>/cancel_user', methods=['POST'])
@jwt_required()
def cancel_user(uid):
    """
    输入类型:
    <uid>       在链接中插入: 用户名

    会完全删除所有的用户信息
        
    返回字段:
    success     注销成功
    error       注销失败
    message     注销失败原因, 只有在注销失败后携带
    """
    current_uid = get_jwt_identity()
    if uid != current_uid:
        return jsonify({"status": "error", "message": "没有权限注销其他的用户"}), 403
    success = RemoveUser(uid)
    if not success:
        return jsonify({"status": "error", "message": "用户注销失败"}), 500
    return jsonify({"status": "success"})

# 查询被Ban的用户
@app.route('/api/baninfo', methods=['GET'])
def get_ban_info():
    """
    输入类型:
    uid         想要查询的用户名

    如果GetBanInfo为空则返回None
    如果GetBanInfo不为空则返回下面格式
    {
        "Reason": "封禁例子",
        "StartTime": "2025-05-01 12:00:00",
        "EndTime": "2025-05-02 08:30:00"
    }
        
    返回字段:
    Reason      封禁内容(封禁原因)
    StartTime   开始封禁时间
    EndTime     结束封禁时间, 如果为None为永久封禁
    Admin       返回用户是否为管理员
    message     如果没有查询到相关用户, 则会返回error且携带message
    """
    uid = request.args.get('uid')
    user = GetUserInfo(uid)
    if user == None:
        return jsonify({"status": "error", "message": "没有该用户的信息"})
    info = GetBanInfo(uid)
    info["Admin"] = user["Admin"]
    return jsonify({"status": "success", "data": info})

# 获取服务器信息
@app.route('/api/server', methods=['GET'])
def get_server_info():
    """
    可以直接对该api进行请求

    如果ServerData获取失败则返回None
    如果ServerData获取成功则返回下面格式
    {
        "PlayerRefs": 0,
        "PlayerCounter": 0,
        "StartupTime": "2000-1-1 00:00:00",
        "Banned": 0,
        "Registered": 0,
        "TickRate": 0
    }
        
    返回字段:
    PlayerRefs      在线用户数量
    PlayerCounter   所有用户在服务器重启后的总登录次数
    StartupTime     服务器开启的时间
    Banned          被Ban玩家的数量
    Registered      总共注册的用户数量
    TickRate        服务器最近的平均Tick, 如果是满Tick则为60.0
    """
    info = ServerData()
    return jsonify({"status": "success", "data": info})

# 获取在线玩家列表
@app.route('/api/players', methods=['GET'])
@jwt_required()
def get_players_list():
    """
    因为上级api限制, 需要登录后可对api请求

    如果PlayerList为空, result_info会接收到[]
    如果PlayerList不为空, result_info会接收到以下格式:
    [
    {"Name": "Example_Test1", "Avatar": "/api/avatar?uid=Example1"},
    {"Name": "Example_Test2", "Avatar": "/api/avatar?uid=Example2"}
    ]
        
    返回字段:
    Name    用户的昵称
    Avatar  返回的Api可以直接获得用户头像的缩略图
    """
    current_uid = get_jwt_identity()
    key = sql.GetKey(current_uid)
    info = PlayerList(key)
    result_info = []
    if info:
        for i in info:
            i_dict = {
                "Name": i["Name"], 
                "Avatar": "/api/avatar?uid=Guest"
                }
            if "Avatar" in i:
                i_dict["Avatar"] = i["Avatar"]
            result_info.append(i_dict)
    return jsonify({"status": "success", "data": result_info})

# 头像修改
@app.route('/api/user/<uid>/upload_avatar', methods=['POST'])
@jwt_required()
def upload_avatar(uid):
    """
    输入类型:
    <uid>       在链接中插入: 用户名
    file        上传的头像文件(图片)

    用户上传头像文件，会自动保存到GlobalAvatar目录并转换为png格式
    然后调用InsertAvatar函数更新用户头像
    
    返回字段:
    success     上传成功
    error       上传失败
    message     失败原因
    """
    current_uid = get_jwt_identity()
    if uid != current_uid:
        return jsonify({"status": "error", "message": "无权修改该用户的头像"}), 403
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "未上传文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "未选择文件"}), 400
    
    if not file.content_type.startswith('image/'):
        return jsonify({"status": "error", "message": "仅支持图片文件"}), 400
    
    try:
        os.makedirs(f"{UserDataPath}/GlobalAvatar", exist_ok=True)

        filename = f"{uid}.png"
        filepath = os.path.join(f"{UserDataPath}/GlobalAvatar", filename)
        file.save(filepath)

        if InsertAvatar(uid):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "更新头像失败"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500