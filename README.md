# 英文文档阅读与翻译助手 (PySide6)

功能
- 导入 .txt、.docx、.pdf 英文文档
- 左侧原文，右侧翻译；段落一一对应
- 左右选择联动、滚动同步
- 多语言目标选择（默认简体中文）
- 翻译基于 deep-translator 的 GoogleTranslator（免密钥，需可访问 Google 网络）。失败会回退原文，保证可用

环境要求
- Windows 10
- Python 3.9+（建议 3.10/3.11）

安装步骤（PowerShell）
1. 创建并激活虚拟环境
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
2. 安装依赖
   pip install -r requirements.txt

运行
python main.py

使用说明
- 点击“打开文件”选择 .txt/.docx/.pdf 文档
- 勾选“自动翻译”时，加载后自动翻译；否则点击“翻译”
- 顶部下拉选择目标语言
- 单击左/右任一段落，对侧会自动选中并定位
- 左右滚动条保持同步

常见问题
- deep-translator 导入失败：pip install deep-translator
- PDF 解析不理想：建议安装/切换 PyMuPDF 或 PyPDF2
- Word 解析失败：pip install python-docx
- 无法访问 Google 导致翻译为空：程序会显示原文，可切换网络或改用其他翻译方案（可后续扩展）

技术说明
- UI: PySide6，QSplitter+QListWidget 实现左右并排
- 子线程翻译：QThread 防阻塞，进度条实时更新
- 分段：按空行/多换行切分，保障段落级对齐