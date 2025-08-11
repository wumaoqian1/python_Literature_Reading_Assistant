import os
from typing import List


def read_txt_file(file_path: str) -> str:
    """
    函数名: read_txt_file
    参数说明:
        file_path (str): 文本文件路径
    返回值说明:
        str: 读取到的文本内容（使用 utf-8，无法解码的字符将被忽略）
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_docx_file(file_path: str) -> str:
    """
    函数名: read_docx_file
    参数说明:
        file_path (str): .docx 文件路径
    返回值说明:
        str: 提取的文档文本（以两个换行分隔段落）
    """
    try:
        from docx import Document  # type: ignore
    except Exception as e:
        raise RuntimeError("缺少依赖 python-docx，请先安装: pip install python-docx") from e

    doc = Document(file_path)
    paragraphs = []
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def read_pdf_file(file_path: str) -> str:
    """
    函数名: read_pdf_file
    参数说明:
        file_path (str): .pdf 文件路径
    返回值说明:
        str: 提取的 PDF 文本（每页以两个换行分隔）
    备注:
        优先使用 PyMuPDF (fitz) 获取更好的布局文本；若不可用则尝试 PyPDF2。
    """
    # 优先尝试 PyMuPDF
    try:
        import fitz  # type: ignore

        text_pages = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text("text")
                text_pages.append(text.strip())
        return "\n\n".join(text_pages)
    except Exception:
        # 回退到 PyPDF2
        try:
            import PyPDF2  # type: ignore

            text_pages = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text() or ""
                    text_pages.append(t.strip())
            return "\n\n".join(text_pages)
        except Exception as e:
            raise RuntimeError(
                "需要安装 PyMuPDF 或 PyPDF2 才能解析 PDF。"
                "建议安装: pip install PyMuPDF\n或回退: pip install PyPDF2"
            ) from e


def read_text_from_file(file_path: str) -> str:
    """
    函数名: read_text_from_file
    参数说明:
        file_path (str): 文件路径（支持 .txt, .docx, .pdf）
    返回值说明:
        str: 提取的纯文本内容
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return read_txt_file(file_path)
    if ext == ".docx":
        return read_docx_file(file_path)
    if ext == ".pdf":
        return read_pdf_file(file_path)
    raise ValueError("仅支持 .txt、.docx、.pdf 格式的文件。")


def split_into_paragraphs(text: str) -> List[str]:
    """
    函数名: split_into_paragraphs
    参数说明:
        text (str): 输入的整体文本
    返回值说明:
        List[str]: 段落列表（按照空行或多换行进行分段，去除首尾空白）
    """
    if not text:
        return []
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = [p.strip() for p in norm.split("\n\n") if p.strip()]
    paragraphs: List[str] = []
    for part in parts:
        chunked = [c.strip() for c in part.split("\n\n") if c.strip()]
        paragraphs.extend(chunked if chunked else [part])
    return paragraphs