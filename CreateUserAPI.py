import os
import yaml
from PIL import Image
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
# 不进行此操作无法登录
def InsertBasicInfo(uid: str):
    config_path = f"{UserDataPath}/User/{uid}/BasicUserInfo.yaml"
    with open(config_path, "rb") as f:
        sql.insert_data(uid=uid, name="BasicUserInfo", data_type=None, stream=f)

# 初始化/修改用户的头像
def InsertAvatar(uid: str):
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
            print(f"全局头像初始错误: {e}")
    else:
        os.makedirs(f"{UserDataPath}/GlobalAvatar")
    try:
        config_path = f"{UserDataPath}/User/{uid}/avatar.png"
        with open(config_path, "rb") as f:
            with sql.write_file(uid, "avatar.png") as stream:
                stream.write(f.read())
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"修改头像失败: {e}")

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
        print(f"修改昵称失败: {e}")
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
        print(f"赋予管理员失败: {e}")
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
        print(f"收回管理员失败: {e}")
        return False