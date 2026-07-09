import yaml
import os


class ConfigManager:
    """配置管理器"""

    _config = None

    @classmethod
    def load_config(cls, env=None):
        """加载配置文件"""
        if cls._config is not None:
            return cls._config

        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 默认配置文件
        config_file = os.path.join(base_dir, 'config', '../config/config.yaml')

        # 如果指定了环境，尝试加载对应环境的配置
        if env:
            env_config_file = os.path.join(base_dir, 'config', f'config.{env}.yaml')
            if os.path.exists(env_config_file):
                config_file = env_config_file

        # 读取 YAML 文件
        with open(config_file, 'r', encoding='utf-8') as f:
            cls._config = yaml.safe_load(f)

        print(f"Config loaded: {config_file}")
        return cls._config

    @classmethod
    def get(cls, key_path, default=None):
        """
        获取配置值，支持点号路径
        例如：get('server.base_url') 获取 server 下的 base_url
        """
        if cls._config is None:
            cls.load_config()

        keys = key_path.split('.')
        value = cls._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    @classmethod
    def set(cls, key_path, value):
        """动态设置配置项"""
        if cls._config is None:
            cls.load_config()

        keys = key_path.split('.')
        data = cls._config
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value

    @classmethod
    def reload(cls):
        """重新加载配置"""
        cls._config = None
        return cls.load_config()


# 全局配置实例
config = ConfigManager()