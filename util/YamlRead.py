import yaml
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    'UserDataPath': '/serverpath/UserData/',
    'real': 'Celeste.Mod',
    'module': 'CelesteNet.Server'
}

_config: Dict[str, Any] = {}

def init_config(config_path: str = 'config.yaml') -> None:
    global _config
    if not os.path.exists(config_path):
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
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(_config, f, sort_keys=False, allow_unicode=True)

def get_config(key: str, default: Any = None) -> Any:
    return _config.get(key, default)

init_config()

UserDataPath = get_config('UserDataPath')
real = get_config('real')
module = get_config('module')