import os
import json
from dataclasses import dataclass
from typing import List, Tuple


# 通用语言项: (显示名, 通用代码, Baidu代码, Youdao代码)
LANG_ITEMS: List[Tuple[str, str, str, str]] = [
    ("简体中文", "zh-CN", "zh", "zh-CHS"),
    ("繁體中文", "zh-TW", "cht", "zh-CHT"),
    ("英语", "en", "en", "en"),
    ("日语", "ja", "jp", "ja"),
    ("韩语", "ko", "kor", "ko"),
    ("法语", "fr", "fra", "fr"),
    ("德语", "de", "de", "de"),
    ("西班牙语", "es", "spa", "es"),
    ("俄语", "ru", "ru", "ru"),
    ("阿拉伯语", "ar", "ara", "ar"),
    ("意大利语", "it", "it", "it"),
    ("葡萄牙语", "pt", "pt", "pt"),
]


def get_baidu_lang(generic: str) -> str:
    """
    函数名: get_baidu_lang
    参数说明:
        generic (str): 通用语言代码，如 'zh-CN', 'ja'
    返回值说明:
        str: Baidu 对应的语言代码，找不到则回退 generic
    """
    for _, g, b, _ in LANG_ITEMS:
        if g == generic:
            return b
    return generic


def get_youdao_lang(generic: str) -> str:
    """
    函数名: get_youdao_lang
    参数说明:
        generic (str): 通用语言代码
    返回值说明:
        str: Youdao 对应的语言代码，找不到则回退 generic
    """
    for _, g, _, y in LANG_ITEMS:
        if g == generic:
            return y
    return generic


@dataclass
class AppConfig:
    """
    函数名: AppConfig
    参数说明:
        provider (str): 翻译引擎标识 'google' | 'baidu' | 'youdao'
        baidu_appid (str): 百度翻译 AppID
        baidu_key (str): 百度翻译 密钥
        youdao_app_key (str): 有道翻译 AppKey
        youdao_app_secret (str): 有道翻译 AppSecret
    返回值说明:
        无（用于保存/加载配置）
    """

    provider: str = "google"
    baidu_appid: str = ""
    baidu_key: str = ""
    youdao_app_key: str = ""
    youdao_app_secret: str = ""

    @staticmethod
    def config_path() -> str:
        """
        函数名: config_path
        参数说明:
            无
        返回值说明:
            str: 配置文件路径
        """
        return os.path.join(os.path.dirname(__file__), "config.json")

    @classmethod
    def load(cls) -> "AppConfig":
        """
        函数名: load
        参数说明:
            无
        返回值说明:
            AppConfig: 从磁盘读取的配置，如不存在则返回默认配置
        """
        path = cls.config_path()
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                provider=data.get("provider", "google"),
                baidu_appid=data.get("baidu_appid", ""),
                baidu_key=data.get("baidu_key", ""),
                youdao_app_key=data.get("youdao_app_key", ""),
                youdao_app_secret=data.get("youdao_app_secret", ""),
            )
        except Exception:
            return cls()

    def save(self) -> None:
        """
        函数名: save
        参数说明:
            无
        返回值说明:
            无（保存配置到磁盘）
        """
        path = self.config_path()
        data = {
            "provider": self.provider,
            "baidu_appid": self.baidu_appid,
            "baidu_key": self.baidu_key,
            "youdao_app_key": self.youdao_app_key,
            "youdao_app_secret": self.youdao_app_secret,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)