import yaml
import os
from typing import Dict, Any
from util.log import _log

DEFAULT_CONFIG = {
    'UserDataPath': '/serverpath/UserData/',
    'real': 'Celeste.Mod',
    'module': 'CelesteNet.Server',
    'CelesteNetApi': 'localhost:17232/api',
    'CelesteNetWebRedirect': 'localhost:17232',
    'WebTitle': 'CelesteNetCN',
    'WebHost': '0.0.0.0',
    'WebPort': '17238',
    'JWT_SECRET_KEY': 'abcdefgh12345678',
    'JWT_ACCESS_TOKEN_EXPIRES_MINUTES': 60,
    'SuperAdmin': None,
    'RemoveSuperAdmin': None
}

_config: Dict[str, Any] = {}

def init_config(config_path: str = 'config.yaml') -> None:
    _log._INFO("[YamlRead]read_config")
    global _config
    if not os.path.exists(config_path):
        _log._INFO("[YamlRead]init_config")
        _config = DEFAULT_CONFIG.copy()
        save_config(config_path)
    else:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f) or {}
        
        updated = False
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in _config:
                _config[key] = default_value
                updated = True
        
        if updated:
            save_config(config_path)

def save_config(config_path: str = 'config.yaml') -> None:
    _log._INFO("[YamlRead]save_config")
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(_config, f, sort_keys=False, allow_unicode=True)

def get_config(key: str, default: Any = None) -> Any:
    return _config.get(key, default)

init_config()

UserDataPath = get_config('UserDataPath')
real = get_config('real')
module = get_config('module')
CelesteNetApi = get_config('CelesteNetApi')
CelesteNetWebRedirect = get_config('CelesteNetWebRedirect')
WebTitle = get_config('WebTitle')
WebHost = get_config('WebHost')
WebPort = get_config('WebPort')
JWT_SECRET_KEY = get_config('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(get_config('JWT_ACCESS_TOKEN_EXPIRES_MINUTES'))
SuperAdmin = get_config('SuperAdmin')
RemoveSuperAdmin = get_config('RemoveSuperAdmin')