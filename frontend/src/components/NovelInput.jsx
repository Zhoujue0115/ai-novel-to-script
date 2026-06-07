import React, { useState, useRef } from "react";
import "./NovelInput.css";

const SAMPLE = {
  title: "雨夜重逢",
  chapters: [
    { index: 1, title: "雨夜归人", content: "林夏拖着行李箱走出车站时，天空正飘着细雨。她已经三年没有回到这座城市了。街灯在水雾中晕开昏黄的光，她抬手遮了遮额头，快步拐进老街尽头的那家咖啡馆。\n\n咖啡馆里只亮着几盏灯，没有别的客人。她点了一杯热美式，在靠窗的位置坐下，望着窗外出神。雨水顺着玻璃窗滑下来，把街景切割成模糊的碎片。" },
    { index: 2, title: "旧事浮现", content: "咖啡馆的门被推开，一个熟悉的声音传入耳中。'好久不见。'\n\n林夏抬起头，看见了周言。他和三年前没有太大变化，只是眉宇间多了几分沉稳。林夏的手指不自觉收紧了杯柄，心跳漏了一拍。\n\n'我没想到会在这里遇见你。'她听见自己的声音有些发干。\n\n周言在她对面坐下，轻声说：'我经常来这里。这三年，一直没有变。'他说着望向窗外，目光像是穿越了雨幕，落回过去。" },
    { index: 3, title: "迟到的解释", content: "'三年前你为什么要走？'周言的声音很轻，但问题却重重地砸在林夏心上。\n\n林夏低下头，咖啡的热气模糊了她的视线。'那时候我觉得自己配不上你。我刚丢了工作，父亲又病重……我不想拖累你。'\n\n她深吸一口气，眼角有些湿润。'我知道这样说很自私。但当时我真的不知道该怎么办。'\n\n周言没有说话，他把手伸过桌面，轻轻覆住了她的手。咖啡馆里的爵士乐悠然地流淌着，雨还在下，但好像不再那么冷了。" },
  ],
};

export default function NovelInput({ onGenerate, loading }) {
  const [title, setTitle] = useState("");
  const [chapters, setChapters] = useState([
    { index: 1, title: "", content: "" },
    { index: 2, title: "", content: "" },
    { index: 3, title: "", content: "" },
  ]);
  const fileRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [totalChapters, setTotalChapters] = useState(null);  // 完整章节数据（不在表单中渲染）
  const [rangeStart, setRangeStart] = useState(1);
  const [rangeEnd, setRangeEnd] = useState(30);

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/script/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.chapters && data.chapters.length > 0) {
        setTitle(data.title);
        setTotalChapters(data.chapters);  // 全部存内存
        // 表单只显示前 5 章供预览
        setChapters(data.chapters.slice(0, 5));
        if (data.chapters.length > 50) {
          setRangeStart(1);
          setRangeEnd(Math.min(30, data.chapters.length));
        }
      }
    } catch (err) {
      console.error("文件上传失败", err);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function loadSample() {
    setTitle(SAMPLE.title);
    setChapters(SAMPLE.chapters);
  }

  function addChapter() {
    setChapters([...chapters, { index: chapters.length + 1, title: "", content: "" }]);
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
    // 大文件用 totalChapters + 范围过滤
    let finalChapters = chapters;
    if (totalChapters && totalChapters.length > 50) {
      finalChapters = totalChapters.slice(rangeStart - 1, rangeEnd);
    } else if (totalChapters && totalChapters.length <= 50) {
      finalChapters = totalChapters;
    }
    onGenerate({ title, chapters: finalChapters });
  }

  const valid = title.trim() && chapters.length >= 3;
  const showRange = totalChapters && totalChapters.length > 50;

  return (
    <form className="novel-input" onSubmit={handleSubmit}>
      <div className="input-header">
        <h2>输入小说</h2>
        <div className="input-actions">
          <input type="file" ref={fileRef} accept=".txt" onChange={handleFileUpload} hidden />
          <button type="button" className="btn-sample" onClick={() => fileRef.current.click()} disabled={uploading}>{uploading ? "上传中..." : "上传 TXT"}</button>
          <button type="button" className="btn-sample" onClick={loadSample}>加载示例</button>
        </div>
      </div>

      <label className="field">
        <span>小说标题</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="输入小说标题" />
      </label>

      <div className="chapters-header">
        <span>章节内容（至少 3 章）</span>
        <button type="button" onClick={addChapter}>+ 添加章节</button>
      </div>

      {totalChapters && totalChapters.length > 5 && (
        <div className="chapter-summary">
          📚 共 <strong>{totalChapters.length}</strong> 章已加载
          {!showRange && <span>（全部用于生成）</span>}
        </div>
      )}

      {showRange && (
        <div className="range-row">
          <span>生成范围</span>
          <div className="range-inputs">
            第 <input type="number" min={1} max={totalChapters.length} value={rangeStart}
              onChange={(e) => setRangeStart(Number(e.target.value))} />
            <span>—</span> 第 <input type="number" min={rangeStart + 1} max={totalChapters.length} value={rangeEnd}
              onChange={(e) => setRangeEnd(Number(e.target.value))} />
            章
          </div>
          <span className="range-hint">共 {totalChapters.length} 章，每批 8 章批量处理</span>
        </div>
      )}

      {chapters.map((ch, i) => (
        <div key={i} className="chapter-card">
          <div className="chapter-header">
            <span>第 {totalChapters ? ch.index : i + 1} 章（预览）</span>
            {chapters.length > 3 && (
              <button type="button" className="btn-remove" onClick={() => removeChapter(i)}>删除</button>
            )}
          </div>
          <input placeholder="章节标题" value={ch.title} onChange={(e) => updateChapter(i, "title", e.target.value)} />
          <textarea rows={6} placeholder="章节正文" value={ch.content} onChange={(e) => updateChapter(i, "content", e.target.value)} />
        </div>
      ))}

      {totalChapters && totalChapters.length > 5 && (
        <p style={{ fontSize: 12, color: "#999", textAlign: "center" }}>
          （仅显示前 5 章预览，共 {totalChapters.length} 章）
        </p>
      )}

      {!totalChapters && chapters.length < 3 && <p className="hint">需要至少 3 个章节才能生成</p>}

      <button type="submit" className="btn-generate" disabled={!valid || loading}>
        {loading && <span className="spinner" />}
        {loading ? "正在生成..." : "生成剧本"}
      </button>
    </form>
  );
}
