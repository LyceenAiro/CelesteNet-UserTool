import os
import shutil
import yaml
from PIL import Image
from datetime import datetime, timedelta
from SqliteModule import SqliteUserData
from YamlRead import UserDataPath, real, module

sql = SqliteUserData(user_data_root=UserDataPath, real=real, module=module)

# 创建一个新的用户
def CreateUserData(uid: str):
    resultKey = sql.Create(uid)
    print(f"用户: {uid}\n绑定密钥: {resultKey}")
    InsertBasicInfo(uid)

# 重置密钥
def ReGetKey(uid: str):
    resultKey = sql.RegetKey(uid)
    print(f"用户: {uid}\n绑定密钥: {resultKey}")

# 初始化/修改用户的实例
def InsertBasicInfo(uid: str):
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    with open(config_path, "rb") as f:
        sql.insert_data(uid=uid, name="BasicUserInfo", data_type=None, stream=f)

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
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"x 全局头像初始错误: {e}")
    else:
        os.makedirs(f"{UserDataPath}/GlobalAvatar")
    try:
        config_path = f"{UserDataPath}/User/{uid}/avatar.png"
        with open(config_path, "rb") as f:
            with sql.write_file(uid, "avatar.png") as stream:
                stream.write(f.read())
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"x 修改头像失败: {e}")
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
        return True
    except Exception as e:
        print(f"x 修改昵称失败: {e}")
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
        return True
    except Exception as e:
        print(f"x 赋予管理员失败: {e}")
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
        return True    
    except Exception as e:
        print(f"x 收回管理员失败: {e}")
        return False
    
# 完全注销用户
def RemoveUser(uid: str) -> bool:
    try:
        if not sql.Wipe(uid):
            return False
        shutil.rmtree(f"{UserDataPath}/User/{uid}")
        print(f"√ 用户数据删除成功")
    except FileNotFoundError:
        pass
    except PermissionError:
        print(f"x 删除用户缓存时发生错误: 权限不足")
    except Exception as e:
        print(f"x 删除用户缓存时发生错误: {e}")
    return True

# 检查Ban信息
def GetBanInfo(uid: str) -> dict:
    data = sql.GetBanData(uid)
    if data is None:
        print("x 没有查询到对应用户信息")
    else:
        print(f"用户名: {uid}\n封禁原因: {data["Reason"]}\n封禁时间: {data["StartTime"]}\n解禁时间: {data["EndTime"]}")
    return data

# 清除Ban记录
def DeBan(uid: str) -> bool:
    data = sql.ClearBanData(uid)
    if data:
        print(f"√ 用户 {uid} Ban记录清空成功")
    else:
        print(f"x 用户 {uid} Ban记录清空失败")
    return data

# 查询用户信息
def GetUserInfo(index: str) -> dict:
    result_dict = {
        "uid": None,
        "key": None,
        "name": None,
        "Avatar": False,
        "Admin": False
    }
    if len(index) == 16 and all(i in '0123456789abcdefABCDEF' for i in index):
        result_dict["key"] = index
        result_dict["uid"] = sql.GetUID(index)
    else:
        result_dict["uid"] = index
        result_dict["key"] = sql.GetKey(index)
    if result_dict["uid"] == "" or result_dict["key"] == "":
        print("x 未匹配到该用户的信息")
        return None
    with open(f"{UserDataPath}/User/{result_dict['uid']}/BasicUserInfo.yaml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    result_dict["name"] = data["Name"]
    if "admin" in data["Tags"]:
        result_dict["Admin"] = True
    if os.path.exists(os.path.join(f"{UserDataPath}/User/{result_dict['uid']}", "avatar.png")):
        result_dict["Avatar"] = True
    return result_dict