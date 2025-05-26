import sqlite3
from script.SqliteModule import SqliteUserData
from util.log import _log
from util.YamlRead import UserDataPath
from util.security import PasswordHelper

sql = SqliteUserData(user_data_root=UserDataPath, real="UserTool", module="Web.User")

def RegisterUser(uid: str, password: str, email: str = None) -> bool:
    """注册用户"""
    salt = PasswordHelper.generate_salt()
    password_hash = PasswordHelper.hash_password(password, salt)
    try:
        with sql.Open() as conn:
            conn.execute("""
                INSERT INTO web_users (uid, password_hash, salt, email)
                VALUES (?, ?, ?, ?)
            """, (uid, password_hash, salt, email))
            conn.commit()
            _log._INFO(f"[RegisterUserWithPassword]√ 用户 {uid} 注册成功")
            return True
    except sqlite3.IntegrityError:
        _log._ERROR(f"[RegisterUserWithPassword]x 用户 {uid} 已存在")
        return False

def VerifyUserPassword(uid: str, password: str) -> bool:
    """验证用户密码"""
    with sql.Open() as conn:
        cursor = conn.execute("""
            SELECT password_hash, salt FROM web_users WHERE uid = ?
        """, (uid,))
        result = cursor.fetchone()
        
        if not result:
            _log._WARN(f"[VerifyUserPassword]x 用户 {uid} 不存在")
            return False
            
        stored_hash, salt = result
        if PasswordHelper.verify_password(password, salt, stored_hash):
            _log._INFO(f"[VerifyUserPassword]√ 用户 {uid} 密码验证成功")
            return True
        else:
            _log._WARN(f"[VerifyUserPassword]x 用户 {uid} 密码验证失败")
            return False

def UpdateUserPassword(uid: str, new_password: str) -> bool:
    """更新用户密码"""
    salt = PasswordHelper.generate_salt()
    new_hash = PasswordHelper.hash_password(new_password, salt)
    
    with sql.Open() as conn:
        conn.execute("""
            UPDATE web_users 
            SET password_hash = ?, salt = ?
            WHERE uid = ?
        """, (new_hash, salt, uid))
        conn.commit()
    _log._INFO(f"[UpdateUserPassword]√ 用户 {uid} 密码更新成功")
    return True
