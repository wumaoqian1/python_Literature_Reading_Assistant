import sys
from typing import List, Optional, Dict
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QComboBox,
    QLabel,
    QCheckBox,
    QProgressBar,
    QMessageBox,
    QSizePolicy,
    QDialog,
)

from config import AppConfig, LANG_ITEMS
from file_readers import read_text_from_file, split_into_paragraphs
from translators import (
    BaseTranslator,
    GoogleWebTranslator,
    BaiduTranslator,
    YoudaoTranslator,
    TranslateTask,
    TranslateWorker,
)
from settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """
    函数名: MainWindow
    参数说明:
        无
    返回值说明:
        无（PySide6 主窗口）
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("英文文档阅读与翻译助手 (PySide6)")
        self.resize(1200, 720)

        # 配置
        self.config = AppConfig.load()

        # 状态
        self.original_paragraphs: List[str] = []
        self.translated_paragraphs: List[str] = []
        self._sync_selecting = False
        self._sync_scrolling = False
        self._current_worker: Optional[TranslateWorker] = None

        # 顶部工具行
        self.open_btn = QPushButton("打开文件")
        self.translate_btn = QPushButton("翻译")
        self.refresh_btn = QPushButton("刷新")
        self.settings_btn = QPushButton("设置")
        self.auto_translate_chk = QCheckBox("自动翻译")
        self.auto_translate_chk.setChecked(True)

        self.lang_combo = QComboBox()
        self._init_language_combo()
        self.engine_label = QLabel()
        self._update_engine_label()

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("目标语言:"))
        top_row.addWidget(self.lang_combo)
        top_row.addSpacing(12)
        top_row.addWidget(self.auto_translate_chk)
        top_row.addStretch(1)
        top_row.addWidget(self.engine_label)
        top_row.addStretch(1)
        top_row.addWidget(self.refresh_btn)
        top_row.addWidget(self.settings_btn)
        top_row.addWidget(self.open_btn)
        top_row.addWidget(self.translate_btn)

        # 中间左右列表
        self.left_list = QListWidget()
        self.right_list = QListWidget()
        self.left_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.right_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.left_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.left_list)
        splitter.addWidget(self.right_list)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # 底部进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # 主布局
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(top_row)
        layout.addWidget(splitter)
        layout.addWidget(self.progress_bar)
        self.setCentralWidget(central)

        # 信号连接
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        self.open_btn.clicked.connect(self.on_open_file_clicked)
        self.translate_btn.clicked.connect(self.on_translate_clicked)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        self.left_list.currentRowChanged.connect(self.on_left_row_changed)
        self.right_list.currentRowChanged.connect(self.on_right_row_changed)
        self.left_list.verticalScrollBar().valueChanged.connect(self.on_left_scroll_changed)
        self.right_list.verticalScrollBar().valueChanged.connect(self.on_right_scroll_changed)

    def _init_language_combo(self) -> None:
        """
        函数名: _init_language_combo
        参数说明:
            无
        返回值说明:
            无（初始化语言下拉选项）
        """
        for label, code, _, _ in LANG_ITEMS:
            self.lang_combo.addItem(f"{label} ({code})", userData=code)
        # 默认简体中文
        default_idx = 0
        self.lang_combo.setCurrentIndex(default_idx)

    def _update_engine_label(self) -> None:
        """
        函数名: _update_engine_label
        参数说明:
            无
        返回值说明:
            无（更新当前引擎标签）
        """
        mapping: Dict[str, str] = {
            "google": "当前引擎: Google Web",
            "baidu": "当前引擎: 百度翻译",
            "youdao": "当前引擎: 有道翻译",
        }
        self.engine_label.setText(mapping.get(self.config.provider, "当前引擎: 未知"))

    @Slot()
    def on_refresh_clicked(self) -> None:
        """
        函数名: on_refresh_clicked
        参数说明:
            无
        返回值说明:
            无（刷新翻译，重新翻译当前文档）
        """
        if self.original_paragraphs:
            self.on_translate_clicked()
        else:
            QMessageBox.information(self, "提示", "请先打开文档。")

    @Slot()
    def on_language_changed(self) -> None:
        """
        函数名: on_language_changed
        参数说明:
            无
        返回值说明:
            无（语言选择改变时，如果开启自动翻译则重新翻译）
        """
        if self.auto_translate_chk.isChecked() and self.original_paragraphs:
            self.on_translate_clicked()

    @Slot()
    def on_settings_clicked(self) -> None:
        """
        函数名: on_settings_clicked
        参数说明:
            无
        返回值说明:
            无（打开设置对话框，保存后更新引擎状态）
        """
        dlg = SettingsDialog(self, self.config)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_engine_label()
            if self.auto_translate_chk.isChecked() and self.original_paragraphs:
                # 设置改变后自动重译
                self.on_translate_clicked()

    @Slot()
    def on_open_file_clicked(self) -> None:
        """
        函数名: on_open_file_clicked
        参数说明:
            无
        返回值说明:
            无（打开文件选择对话框并加载文档）
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择英文文档",
            "",
            "支持格式 (*.txt *.docx *.pdf);;文本 (*.txt);;Word (*.docx);;PDF (*.pdf)",
        )
        if not file_path:
            return
        self.load_document(file_path)

    def load_document(self, file_path: str) -> None:
        """
        函数名: load_document
        参数说明:
            file_path (str): 文件路径
        返回值说明:
            无（读取文档，填充左侧列表，视情况自动触发翻译）
        """
        try:
            text = read_text_from_file(file_path)
        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"文件读取失败：\n{e}")
            return

        self.original_paragraphs = split_into_paragraphs(text)
        if not self.original_paragraphs:
            QMessageBox.information(self, "提示", "未在文档中提取到文本内容。")
            self.left_list.clear()
            self.right_list.clear()
            self.progress_bar.setValue(0)
            return

        self._fill_list(self.left_list, self.original_paragraphs)
        self.right_list.clear()
        self.translated_paragraphs = []
        self.progress_bar.setValue(0)

        if self.auto_translate_chk.isChecked():
            self.on_translate_clicked()

    def _fill_list(self, widget: QListWidget, paragraphs: List[str]) -> None:
        """
        函数名: _fill_list
        参数说明:
            widget (QListWidget): 目标列表控件
            paragraphs (List[str]): 要填充的段落列表
        返回值说明:
            无（将段落逐条加入列表）
        """
        widget.clear()
        for p in paragraphs:
            item = QListWidgetItem(p)
            item.setToolTip(p[:500])
            widget.addItem(item)

    @Slot()
    def on_translate_clicked(self) -> None:
        """
        函数名: on_translate_clicked
        参数说明:
            无
        返回值说明:
            无（根据设置选择翻译器并启动线程）
        """
        if not self.original_paragraphs:
            QMessageBox.information(self, "提示", "请先打开文档。")
            return

        target_code = self.lang_combo.currentData()
        if not target_code:
            QMessageBox.warning(self, "错误", "未选择目标语言。")
            return

        translator = self._build_translator()
        if translator is None:
            return

        self.translate_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        task = TranslateTask(self.original_paragraphs, str(target_code))
        self._current_worker = TranslateWorker(task, translator)
        self._current_worker.progress.connect(self.on_translate_progress)
        self._current_worker.finished_with_result.connect(self.on_translate_finished)
        self._current_worker.failed.connect(self.on_translate_failed)
        self._current_worker.finished.connect(self.on_worker_finished)
        self._current_worker.start()

    def _build_translator(self) -> Optional[BaseTranslator]:
        """
        函数名: _build_translator
        参数说明:
            无
        返回值说明:
            BaseTranslator | None: 根据当前设置构建翻译器，若凭据缺失则提示并返回 None
        """
        provider = self.config.provider
        if provider == "google":
            return GoogleWebTranslator()
        if provider == "baidu":
            if not self.config.baidu_appid or not self.config.baidu_key:
                QMessageBox.warning(self, "缺少凭据", "请先在设置中填写 Baidu AppID 与 Key。")
                return None
            return BaiduTranslator(self.config.baidu_appid, self.config.baidu_key)
        if provider == "youdao":
            if not self.config.youdao_app_key or not self.config.youdao_app_secret:
                QMessageBox.warning(self, "缺少凭据", "请先在设置中填写 Youdao AppKey 与 AppSecret。")
                return None
            return YoudaoTranslator(self.config.youdao_app_key, self.config.youdao_app_secret)
        QMessageBox.warning(self, "错误", f"未知的翻译引擎: {provider}")
        return None

    @Slot(int, int)
    def on_translate_progress(self, done: int, total: int) -> None:
        """
        函数名: on_translate_progress
        参数说明:
            done (int): 已完成数量
            total (int): 总数量
        返回值说明:
            无（更新进度条）
        """
        if total <= 0:
            self.progress_bar.setValue(0)
            return
        percent = int(done * 100 / total)
        self.progress_bar.setValue(min(max(percent, 0), 100))

    @Slot(list)
    def on_translate_finished(self, translated_list: List[str]) -> None:
        """
        函数名: on_translate_finished
        参数说明:
            translated_list (List[str]): 翻译后的段落列表
        返回值说明:
            无（填充右侧列表并初始化对应选中）
        """
        self.translated_paragraphs = translated_list
        self._fill_list(self.right_list, translated_list)
        if self.left_list.count() > 0:
            self.left_list.setCurrentRow(0)
        if self.right_list.count() > 0:
            self.right_list.setCurrentRow(0)

    @Slot(str)
    def on_translate_failed(self, message: str) -> None:
        """
        函数名: on_translate_failed
        参数说明:
            message (str): 错误信息
        返回值说明:
            无（弹出错误提示）
        """
        QMessageBox.critical(self, "翻译失败", f"翻译过程中发生错误：\n{message}")

    @Slot()
    def on_worker_finished(self) -> None:
        """
        函数名: on_worker_finished
        参数说明:
            无
        返回值说明:
            无（翻译线程结束后的 UI 恢复）
        """
        self.translate_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.open_btn.setEnabled(True)

    @Slot(int)
    def on_left_row_changed(self, row: int) -> None:
        """
        函数名: on_left_row_changed
        参数说明:
            row (int): 左侧当前选中行
        返回值说明:
            无（联动右侧选中同一行）
        """
        if self._sync_selecting:
            return
        self._sync_selecting = True
        try:
            if 0 <= row < self.right_list.count():
                self.right_list.setCurrentRow(row)
                if self.right_list.item(row):
                    self.right_list.scrollToItem(self.right_list.item(row))
        finally:
            self._sync_selecting = False

    @Slot(int)
    def on_right_row_changed(self, row: int) -> None:
        """
        函数名: on_right_row_changed
        参数说明:
            row (int): 右侧当前选中行
        返回值说明:
            无（联动左侧选中同一行）
        """
        if self._sync_selecting:
            return
        self._sync_selecting = True
        try:
            if 0 <= row < self.left_list.count():
                self.left_list.setCurrentRow(row)
                self.left_list.scrollToItem(self.left_list.item(row))
        finally:
            self._sync_selecting = False

    @Slot(int)
    def on_left_scroll_changed(self, value: int) -> None:
        """
        函数名: on_left_scroll_changed
        参数说明:
            value (int): 左侧滚动条值
        返回值说明:
            无（同步右侧滚动条）
        """
        if self._sync_scrolling:
            return
        self._sync_scrolling = True
        try:
            left_sb = self.left_list.verticalScrollBar()
            right_sb = self.right_list.verticalScrollBar()
            if left_sb.maximum() > 0:
                ratio = value / max(1, left_sb.maximum())
                right_value = int(ratio * right_sb.maximum())
                right_sb.setValue(right_value)
        finally:
            self._sync_scrolling = False

    @Slot(int)
    def on_right_scroll_changed(self, value: int) -> None:
        """
        函数名: on_right_scroll_changed
        参数说明:
            value (int): 右侧滚动条值
        返回值说明:
            无（同步左侧滚动条）
        """
        if self._sync_scrolling:
            return
        self._sync_scrolling = True
        try:
            right_sb = self.right_list.verticalScrollBar()
            left_sb = self.left_list.verticalScrollBar()
            if right_sb.maximum() > 0:
                ratio = value / max(1, right_sb.maximum())
                left_value = int(ratio * left_sb.maximum())
                left_sb.setValue(left_value)
        finally:
            self._sync_scrolling = False


def show_dependency_tips() -> None:
    """
    函数名: show_dependency_tips
    参数说明:
        无
    返回值说明:
        无（在控制台打印依赖提示）
    """
    print(
        "提示: 如遇到导入失败，请安装依赖:\n"
        "  pip install -r requirements.txt\n"
        "本程序依赖: PySide6, python-docx, PyMuPDF 或 PyPDF2, deep-translator, requests\n"
        "在'设置'中可配置 百度/有道 的凭据。\n"
    )


def main() -> None:
    """
    函数名: main
    参数说明:
        无
    返回值说明:
        无（应用入口，启动 PySide6 主窗口）
    """
    show_dependency_tips()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()