import { useState } from "react";
import "./NovelInput.css";

export default function NovelInput({ onGenerate, loading }) {
  const [title, setTitle] = useState("");
  const [chapters, setChapters] = useState([
    { index: 1, title: "", content: "" },
    { index: 2, title: "", content: "" },
    { index: 3, title: "", content: "" },
  ]);

  function addChapter() {
    setChapters([
      ...chapters,
      { index: chapters.length + 1, title: "", content: "" },
    ]);
  }

  function removeChapter(i) {
    if (chapters.length <= 3) return;
    const next = chapters.filter((_, idx) => idx !== i);
    setChapters(next.map((ch, idx) => ({ ...ch, index: idx + 1 })));
  }

  function updateChapter(i, field, value) {
    const next = [...chapters];
    next[i] = { ...next[i], [field]: value };
    setChapters(next);
  }

  function handleSubmit(e) {
    e.preventDefault();
    onGenerate({ title, chapters });
  }

  const valid = title.trim() && chapters.length >= 3;

  return (
    <form className="novel-input" onSubmit={handleSubmit}>
      <h2>输入小说</h2>

      <label className="field">
        <span>小说标题</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="输入小说标题" />
      </label>

      <div className="chapters-header">
        <span>章节内容（至少 3 章）</span>
        <button type="button" onClick={addChapter}>+ 添加章节</button>
      </div>

      {chapters.map((ch, i) => (
        <div key={i} className="chapter-card">
          <div className="chapter-header">
            <span>第 {i + 1} 章</span>
            {chapters.length > 3 && (
              <button type="button" className="btn-remove" onClick={() => removeChapter(i)}>删除</button>
            )}
          </div>
          <input
            placeholder="章节标题"
            value={ch.title}
            onChange={(e) => updateChapter(i, "title", e.target.value)}
          />
          <textarea
            rows={6}
            placeholder="章节正文"
            value={ch.content}
            onChange={(e) => updateChapter(i, "content", e.target.value)}
          />
        </div>
      ))}

      {chapters.length < 3 && (
        <p className="hint">需要至少 3 个章节才能生成</p>
      )}

      <button type="submit" className="btn-generate" disabled={!valid || loading}>
        {loading ? "生成中..." : "生成剧本"}
      </button>
    </form>
  );
}
