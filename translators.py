import time
import random
import hashlib
from dataclasses import dataclass
from typing import List
import requests
from PySide6.QtCore import QThread, Signal

from config import get_baidu_lang, get_youdao_lang


class BaseTranslator:
    """
    函数名: BaseTranslator
    参数说明:
        无
    返回值说明:
        无（翻译器接口类）
    """

    def translate_many(self, texts: List[str], target: str, progress_cb=None) -> List[str]:
        """
        函数名: translate_many
        参数说明:
            texts (List[str]): 待翻译文本列表
            target (str): 通用目标语言代码
            progress_cb (Callable[[int, int], None] | None): 进度回调
        返回值说明:
            List[str]: 逐项翻译后的文本（失败项回退原文）
        """
        raise NotImplementedError


class GoogleWebTranslator(BaseTranslator):
    """
    函数名: GoogleWebTranslator
    参数说明:
        无
    返回值说明:
        无（使用 deep-translator 的 GoogleTranslator）
    """

    def __init__(self) -> None:
        self._ready = False
        self._err = None
        try:
            from deep_translator import GoogleTranslator  # type: ignore

            self.GoogleTranslator = GoogleTranslator
            self._ready = True
        except Exception as e:
            self._ready = False
            self._err = e

    def translate_text(self, text: str, target: str) -> str:
        """
        函数名: translate_text
        参数说明:
            text (str): 源文本
            target (str): 通用目标语言代码，如 'zh-CN'
        返回值说明:
            str: 翻译结果（失败回退原文）
        """
        if not text.strip():
            return text
        if not self._ready:
            return text
        try:
            translator = self.GoogleTranslator(source="auto", target=target)
            return translator.translate(text)
        except Exception:
            return text

    def translate_many(self, texts: List[str], target: str, progress_cb=None) -> List[str]:
        """
        函数名: translate_many
        参数说明:
            texts (List[str]): 待翻译列表
            target (str): 通用目标语言代码
            progress_cb (Callable[[int, int], None] | None): 进度回调
        返回值说明:
            List[str]: 翻译结果列表
        """
        results: List[str] = []
        total = len(texts)
        for i, t in enumerate(texts, start=1):
            results.append(self.translate_text(t, target))
            if progress_cb:
                try:
                    progress_cb(i, total)
                except Exception:
                    pass
        return results


class BaiduTranslator(BaseTranslator):
    """
    函数名: BaiduTranslator
    参数说明:
        appid (str): 百度翻译 AppID
        key (str): 百度翻译 Key
    返回值说明:
        无（通过官方 Trans API 进行翻译）
    参考:
        https://api.fanyi.baidu.com/product/113
        接口: https://fanyi-api.baidu.com/api/trans/vip/translate
        签名: MD5(appid+q+salt+key)
    """

    def __init__(self, appid: str, key: str) -> None:
        self.appid = appid
        self.key = key
        self.endpoint = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def _sign(self, q: str, salt: str) -> str:
        """
        函数名: _sign
        参数说明:
            q (str): 待翻译文本
            salt (str): 随机盐
        返回值说明:
            str: md5 签名
        """
        raw = f"{self.appid}{q}{salt}{self.key}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _translate_once(self, text: str, target_generic: str) -> str:
        """
        函数名: _translate_once
        参数说明:
            text (str): 单条文本
            target_generic (str): 通用目标语言代码
        返回值说明:
            str: 翻译结果（失败回退原文）
        """
        if not text.strip():
            return text
        salt = str(random.randint(100000, 999999))
        params = {
            "q": text,
            "from": "auto",
            "to": get_baidu_lang(target_generic),
            "appid": self.appid,
            "salt": salt,
            "sign": self._sign(text, salt),
        }
        try:
            resp = requests.post(self.endpoint, data=params, timeout=15)
            data = resp.json()
            if "error_code" in data:
                return text
            trans = data.get("trans_result", [])
            if not trans:
                return text
            return trans[0].get("dst", text) or text
        except Exception:
            return text

    def translate_many(self, texts: List[str], target: str, progress_cb=None) -> List[str]:
        """
        函数名: translate_many
        参数说明:
            texts (List[str]): 待翻译列表
            target (str): 通用目标语言代码
            progress_cb (Callable[[int, int], None] | None): 进度回调
        返回值说明:
            List[str]: 翻译结果列表
        """
        results: List[str] = []
        total = len(texts)
        for i, t in enumerate(texts, start=1):
            results.append(self._translate_once(t, target))
            if progress_cb:
                try:
                    progress_cb(i, total)
                except Exception:
                    pass
        return results


class YoudaoTranslator(BaseTranslator):
    """
    函数名: YoudaoTranslator
    参数说明:
        app_key (str): 有道翻译 AppKey
        app_secret (str): 有道翻译 AppSecret
    返回值说明:
        无（使用有道开放平台 V3 签名）
    参考:
        https://ai.youdao.com/DOCSIRMA/html/%E6%96%87%E6%9C%AC%E7%BF%BB%E8%AF%91/api/%E6%96%87%E6%9C%AC%E7%BF%BB%E8%AF%91%E6%8E%A5%E5%8F%A3v3.html
        接口: https://openapi.youdao.com/api
        signType=v3, sign=SHA256(appKey+input+salt+curtime+appSecret)
    """

    def __init__(self, app_key: str, app_secret: str) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.endpoint = "https://openapi.youdao.com/api"

    def _truncate(self, q: str) -> str:
        """
        函数名: _truncate
        参数说明:
            q (str): 原文
        返回值说明:
            str: 计算签名用的 input 值
        """
        if q is None:
            return ""
        size = len(q)
        return q if size <= 20 else q[:10] + str(size) + q[-10:]

    def _sign(self, q: str, salt: str, curtime: str) -> str:
        """
        函数名: _sign
        参数说明:
            q (str): 原文
            salt (str): 随机盐
            curtime (str): 当前时间戳（秒）
        返回值说明:
            str: sha256 签名十六进制
        """
        sign_str = self.app_key + self._truncate(q) + salt + curtime + self.app_secret
        return hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

    def _translate_once(self, text: str, target_generic: str) -> str:
        """
        函数名: _translate_once
        参数说明:
            text (str): 单条文本
            target_generic (str): 通用目标语言代码
        返回值说明:
            str: 翻译结果（失败回退原文）
        """
        if not text.strip():
            return text
        salt = str(random.randint(100000, 999999))
        curtime = str(int(time.time()))
        payload = {
            "q": text,
            "from": "auto",
            "to": get_youdao_lang(target_generic),
            "appKey": self.app_key,
            "salt": salt,
            "signType": "v3",
            "curtime": curtime,
            "sign": self._sign(text, salt, curtime),
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            resp = requests.post(self.endpoint, data=payload, headers=headers, timeout=15)
            data = resp.json()
            if data.get("errorCode") != "0":
                return text
            trans = data.get("translation", [])
            if not trans:
                return text
            return trans[0] or text
        except Exception:
            return text

    def translate_many(self, texts: List[str], target: str, progress_cb=None) -> List[str]:
        """
        函数名: translate_many
        参数说明:
            texts (List[str]): 待翻译列表
            target (str): 通用目标语言代码
            progress_cb (Callable[[int, int], None] | None): 进度回调
        返回值说明:
            List[str]: 翻译结果列表
        """
        results: List[str] = []
        total = len(texts)
        for i, t in enumerate(texts, start=1):
            results.append(self._translate_once(t, target))
            if progress_cb:
                try:
                    progress_cb(i, total)
                except Exception:
                    pass
        return results


@dataclass
class TranslateTask:
    """
    函数名: TranslateTask
    参数说明:
        paragraphs (List[str]): 待翻译段落
        target_lang (str): 通用目标语言代码
    返回值说明:
        无（数据类封装任务）
    """

    paragraphs: List[str]
    target_lang: str


class TranslateWorker(QThread):
    """
    函数名: TranslateWorker
    参数说明:
        task (TranslateTask): 翻译任务
        translator (BaseTranslator): 翻译器实例
    返回值说明:
        无（通过信号返回进度与结果）
    """

    progress = Signal(int, int)  # done, total
    finished_with_result = Signal(list)
    failed = Signal(str)

    def __init__(self, task: TranslateTask, translator: BaseTranslator) -> None:
        super().__init__()
        self.task = task
        self.translator = translator

    def run(self) -> None:
        """
        函数名: run
        参数说明:
            无
        返回值说明:
            无（线程执行翻译）
        """
        try:
            result = self.translator.translate_many(
                self.task.paragraphs,
                self.task.target_lang,
                progress_cb=lambda d, t: self.progress.emit(d, t),
            )
            self.finished_with_result.emit(result)
        except Exception as e:
            self.failed.emit(str(e))