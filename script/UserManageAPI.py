import os
import shutil
import yaml
from PIL import Image

from script.SqliteModule import SqliteUserData
from script.WebUserManage import RegisterUser, VerifyUserPassword, UpdateUserPassword

from util.log import _log
from util.YamlRead import UserDataPath, real, module
from util.security import PasswordHelper

sql = SqliteUserData(user_data_root=UserDataPath, real=real, module=module)

# 创建一个新的用户
def CreateUserData(uid: str, pwd: str) -> list:
    if not RegisterUser(uid, pwd):
        return
    resultKey = sql.Create(uid)
    if not resultKey:
        _log._ERROR(f"[CreateUserData]x 新建用户失败, 用户 {uid} 已被注册")
        return False
    _log._INFO(f"[CreateUserData]√ 新建用户成功, 用户 {uid} 绑定密钥: {resultKey}")
    InsertBasicInfo(uid)
    return [uid, resultKey]

# 重置密钥
def ReGetKey(uid: str) -> str:
    resultKey = sql.RegetKey(uid)
    _log._INFO(f"[ReGetKey]√ 重置密钥成功, 用户 {uid} 绑定密钥: {resultKey}")
    return resultKey

# 初始化/修改用户的实例
def InsertBasicInfo(uid: str):
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    with open(config_path, "rb") as f:
        sql.insert_data(uid=uid, name="BasicUserInfo", data_type=None, stream=f)
    _log._INFO(f"[InsertBasicInfo]√ 用户 {uid} 实例操作成功")

# 初始化/修改用户的头像
def InsertAvatar(uid: str) -> bool:
    # 尝试从全局头像中快速绑定头像并更改64x64
    if os.path.exists(f"{UserDataPath}/GlobalAvatar"):
        try:
            with Image.open(f"{UserDataPath}/GlobalAvatar/{uid}.png") as img:
                img.resize((64, 64), Image.Resampling.LANCZOS).save(
                    f"{UserDataPath}/User/{uid}/avatar.png",
                    'PNG',
                    optimize=True
                )
            _log._INFO(f"[InsertAvatar]√ 用户 {uid} 全局头像初始成功")
        except FileNotFoundError:
            pass
        except Exception as e:
            _log._ERROR(f"[InsertAvatar]x 用户 {uid} 全局头像初始错误: {e}")
    else:
        os.makedirs(f"{UserDataPath}/GlobalAvatar")
    try:
        config_path = f"{UserDataPath}/User/{uid}/avatar.png"
        with open(config_path, "rb") as f:
            with sql.write_file(uid, "avatar.png") as stream:
                stream.write(f.read())
        _log._INFO(f"[InsertAvatar]√ 用户 {uid} 头像修改成功")
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        _log._ERROR(f"[InsertAvatar]x 用户 {uid} 修改头像失败: {e}")
        return False

# 修改昵称
def ChangeName(uid: str, name: str) -> bool:
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        data['Name'] = name
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        InsertBasicInfo(uid)
        _log._INFO(f"[ChangeName]√ {uid} 修改昵称 {name} 成功")
        return True
    except Exception as e:
        _log._ERROR(f"[ChangeName]x {uid} 修改昵称 {name} 失败: {e}")
        return False

# 赋予玩家管理员
def GiveOP(uid: str) -> bool:
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        if 'admin' not in data['Tags']:
            data['Tags'].append('admin')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        InsertBasicInfo(uid)
        _log._INFO(f"[GiveOP]√ {uid} 赋予管理员成功")
        return True
    except Exception as e:
        _log._ERROR(f"[GiveOP]x {uid} 赋予管理员失败: {e}")
        return False

# 移除玩家管理员
def DeOP(uid: str) -> bool:
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        if 'Tags' in data and 'admin' in data['Tags']:
            data['Tags'].remove('admin')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        InsertBasicInfo(uid)
        _log._INFO(f"[DeOP]√ {uid} 回收管理员成功")
        return True    
    except Exception as e:
        _log._ERROR(f"[DeOP]x {uid} 回收管理员失败: {e}")
        return False
    
# 完全注销用户
def RemoveUser(uid: str) -> bool:
    try:
        if not sql.Wipe(uid):
            return False
        _log._INFO(f"[RemoveUser]√ 用户 {uid} 数据删除成功")
        shutil.rmtree(f"{UserDataPath}/User/{uid}")
        _log._INFO(f"[RemoveUser]√ 用户 {uid} 缓存删除成功")
    except FileNotFoundError:
        pass
    except PermissionError:
        _log._WARN(f"[RemoveUser]x 删除用户 {uid} 缓存时发生错误: 权限不足")
    except Exception as e:
        _log._WARN(f"[RemoveUser]x 删除用户 {uid} 缓存时发生错误: {e}")
    return True

# 检查Ban信息
def GetBanInfo(uid: str) -> dict:
    data = sql.GetBanData(uid)
    _log._INFO(f"[GetBanInfo]uid: {uid} BanInfo: {data}")
    return data

# 清除Ban记录
def DeBan(uid: str) -> bool:
    data = sql.ClearBanData(uid)
    if data:
        _log._INFO(f"[DeBan]√ 用户 {uid} Ban记录清空成功")
    else:
        _log._ERROR(f"[DeBan]x 用户 {uid} Ban记录清空失败")
    return data

# 查询用户信息
def GetUserInfo(index: str) -> dict:
    result_dict = {
        "uid": None,
        "key": None,
        "name": None,
        "Avatar": False,
        "Admin": False,
        "Email": None
    }
    if len(index) == 16 and all(i in '0123456789abcdefABCDEF' for i in index):
        result_dict["key"] = index
        result_dict["uid"] = sql.GetUID(index)
    else:
        result_dict["uid"] = index
        result_dict["key"] = sql.GetKey(index)
    if result_dict["uid"] == "" or result_dict["key"] == "":
        _log._WARN(f"[GetUserInfo]x 未匹配到索引 {index} 的信息")
        return None
    with sql.Open() as conn:
        cursor = conn.execute("""
            SELECT email FROM web_users WHERE uid = ?
        """, (result_dict["uid"],))
        pwd_result = cursor.fetchone()
        if pwd_result:
            result_dict["Email"] = pwd_result[0]
    with open(f"{UserDataPath}/User/{result_dict['uid']}/BasicUserInfo.yaml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    result_dict["name"] = data["Name"]
    if "admin" in data["Tags"]:
        result_dict["Admin"] = True
    if os.path.exists(os.path.join(f"{UserDataPath}/User/{result_dict['uid']}", "avatar.png")):
        result_dict["Avatar"] = True
    _log._INFO(f"[GetUserInfo]{result_dict}")
    return result_dict

def is_CheckAdmin(uid: str) -> bool:
    with open(f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    if "admin" in data["Tags"]:
        return True
    return False