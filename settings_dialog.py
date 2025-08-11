from typing import Optional
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)

from config import AppConfig


class SettingsDialog(QDialog):
    """
    函数名: SettingsDialog
    参数说明:
        parent (QWidget | None): 父组件
        config (AppConfig): 当前配置
    返回值说明:
        无（用于编辑翻译器配置）
    """

    def __init__(self, parent: Optional[QWidget], config: AppConfig) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置 | 翻译引擎与凭据")
        self.config = config

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Google Web（deep-translator）", userData="google")
        self.provider_combo.addItem("百度翻译（需 AppID/Key）", userData="baidu")
        self.provider_combo.addItem("有道翻译（需 AppKey/AppSecret）", userData="youdao")

        # 凭据输入框
        self.baidu_appid_edit = QLineEdit()
        self.baidu_key_edit = QLineEdit()
        self.baidu_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.youdao_key_edit = QLineEdit()
        self.youdao_secret_edit = QLineEdit()
        self.youdao_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("翻译引擎", self.provider_combo)
        form.addRow("Baidu AppID", self.baidu_appid_edit)
        form.addRow("Baidu Key", self.baidu_key_edit)
        form.addRow("Youdao AppKey", self.youdao_key_edit)
        form.addRow("Youdao AppSecret", self.youdao_secret_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save_clicked)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._load_to_ui()
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self._on_provider_changed(self.provider_combo.currentIndex())

    def _load_to_ui(self) -> None:
        """
        函数名: _load_to_ui
        参数说明:
            无
        返回值说明:
            无（将现有配置填充到 UI）
        """
        # provider
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == self.config.provider:
                self.provider_combo.setCurrentIndex(i)
                break
        # baidu
        self.baidu_appid_edit.setText(self.config.baidu_appid)
        self.baidu_key_edit.setText(self.config.baidu_key)
        # youdao
        self.youdao_key_edit.setText(self.config.youdao_app_key)
        self.youdao_secret_edit.setText(self.config.youdao_app_secret)

    def _on_provider_changed(self, _index: int) -> None:
        """
        函数名: _on_provider_changed
        参数说明:
            _index (int): 下拉索引
        返回值说明:
            无（根据选择显示/隐藏对应凭据项）
        """
        provider = self.provider_combo.currentData()
        is_baidu = provider == "baidu"
        is_youdao = provider == "youdao"
        # 显隐控制
        self._set_row_visible(self.baidu_appid_edit, is_baidu)
        self._set_row_visible(self.baidu_key_edit, is_baidu)
        self._set_row_visible(self.youdao_key_edit, is_youdao)
        self._set_row_visible(self.youdao_secret_edit, is_youdao)

    def _set_row_visible(self, widget: QWidget, visible: bool) -> None:
        """
        函数名: _set_row_visible
        参数说明:
            widget (QWidget): 要控制的控件
            visible (bool): 是否可见
        返回值说明:
            无（设置行可见性）
        """
        widget.setVisible(visible)
        # 获取对应的标签并设置可见性
        form_layout = widget.parent().layout()
        if hasattr(form_layout, 'labelForField'):
            label = form_layout.labelForField(widget)
            if label:
                label.setVisible(visible)

    def _on_save_clicked(self) -> None:
        """
        函数名: _on_save_clicked
        参数说明:
            无
        返回值说明:
            无（校验并保存配置）
        """
        provider = self.provider_combo.currentData()
        # 校验必填
        if provider == "baidu":
            if not self.baidu_appid_edit.text().strip() or not self.baidu_key_edit.text().strip():
                QMessageBox.warning(self, "缺少凭据", "请填写 Baidu AppID 与 Key。")
                return
        if provider == "youdao":
            if not self.youdao_key_edit.text().strip() or not self.youdao_secret_edit.text().strip():
                QMessageBox.warning(self, "缺少凭据", "请填写 Youdao AppKey 与 AppSecret。")
                return

        # 保存
        self.config.provider = provider
        self.config.baidu_appid = self.baidu_appid_edit.text().strip()
        self.config.baidu_key = self.baidu_key_edit.text().strip()
        self.config.youdao_app_key = self.youdao_key_edit.text().strip()
        self.config.youdao_app_secret = self.youdao_secret_edit.text().strip()
        try:
            self.config.save()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置失败：\n{e}")
            return
        self.accept()