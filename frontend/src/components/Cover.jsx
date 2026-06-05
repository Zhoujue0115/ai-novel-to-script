import React from "react";
import "./Cover.css";

export default function Cover({ onEnter }) {
  return (
    <div className="cover">
      <div className="cover-content">
        <div className="cover-icon">---</div>
        <h1>AI 小说转剧本工具</h1>
        <p className="cover-sub">将小说章节一键转为结构化 YAML 格式剧本</p>
        <div className="cover-features">
          <span>角色提取</span>
          <span>场景拆分</span>
          <span>对白重组</span>
          <span>YAML 导出</span>
        </div>
        <button className="cover-enter" onClick={onEnter}>开始使用</button>
      </div>
      <div className="cover-footer">输入 3 章以上小说 · 自动生成剧本初稿</div>
    </div>
  );
}
