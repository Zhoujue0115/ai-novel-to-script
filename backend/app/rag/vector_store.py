"""ChromaDB 向量存储 —— 小说全文索引"""

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from ..logger import get_logger

logger = get_logger(__name__)

# 用轻量中文模型
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "novel_chapters"
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

_model = None
_client = None


def _get_model():
    global _model
    if _model is None:
        logger.info(f"加载 embedding 模型: {EMBED_MODEL_NAME}")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def _get_client():
    global _client
    if _client is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
    return _client


def index_chapters(title: str, chapters: list, force_rebuild: bool = False) -> str:
    """将小说章节向量化存入 ChromaDB，返回 collection 名称"""
    client = _get_client()
    model = _get_model()

    # 用标题生成唯一 collection 名
    safe_name = "".join(c for c in title if c.isalnum() or c in "_ -")[:40].strip()
    col_name = f"novel_{safe_name}" if safe_name else COLLECTION_NAME

    if force_rebuild:
        try:
            client.delete_collection(col_name)
        except Exception:
            pass

    try:
        col = client.get_collection(col_name)
        count = col.count()
        if count > 0:
            logger.info(f"集合 {col_name} 已有 {count} 条记录，复用索引")
            return col_name
    except Exception:
        pass

    col = client.create_collection(col_name, metadata={"title": title, "chapter_count": len(chapters)})

    docs, metadatas, ids = [], [], []
    for ch in chapters:
        # 每章拆成段落（按空行）
        paragraphs = [p.strip() for p in ch["content"].split("\n\n") if p.strip()]
        for pi, para in enumerate(paragraphs):
            if len(para) < 10:
                continue
            doc_id = f"ch{ch['index']}_p{pi}"
            docs.append(para)
            metadatas.append({
                "chapter_index": ch["index"],
                "chapter_title": ch["title"],
                "paragraph_index": pi,
            })
            ids.append(doc_id)

    if not docs:
        logger.warning("没有可索引的段落")
        return col_name

    logger.info(f"向量化 {len(docs)} 个段落...")
    embeddings = model.encode(docs, show_progress_bar=False).tolist()

    col.add(embeddings=embeddings, documents=docs, metadatas=metadatas, ids=ids)
    logger.info(f"索引完成: {len(docs)} 段 → {col_name}")
    return col_name


def search_chapters(title: str, query: str, top_k: int = 5) -> list[str]:
    """根据查询检索相关小说段落"""
    client = _get_client()
    model = _get_model()

    safe_name = "".join(c for c in title if c.isalnum() or c in "_ -")[:40].strip()
    col_name = f"novel_{safe_name}" if safe_name else COLLECTION_NAME

    try:
        col = client.get_collection(col_name)
    except Exception:
        logger.warning(f"集合 {col_name} 不存在，请先建索引")
        return []

    q_embedding = model.encode([query], show_progress_bar=False).tolist()
    results = col.query(query_embeddings=q_embedding, n_results=min(top_k, col.count()))

    passages = []
    for i, doc in enumerate(results.get("documents", [[]])[0]):
        meta = results.get("metadatas", [[]])[0][i] if i < len(results.get("metadatas", [[]])[0]) else {}
        passages.append(f"[第{meta.get('chapter_index','?')}章] {doc}")

    logger.info(f"检索 '{query[:30]}...' → {len(passages)} 条结果")
    return passages
