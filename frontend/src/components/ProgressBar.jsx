import React from "react";
import "./ProgressBar.css";

export default function ProgressBar({ step, message, batches }) {
  if (!step || step === "done") return null;

  // 批量模式：每条批次独立一行
  if (step === "batch" && batches) {
    const done = batches.filter((b) => b.status === "done").length;
    const pct = batches.length > 0 ? Math.round((done / batches.length) * 100) : 0;
    return (
      <div className="progress-bar">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="batch-list">
          {batches.map((b, i) => (
            <div key={i} className={`batch-item ${b.status}`}>
              <span className="batch-icon">{b.status === "done" ? "✅" : b.status === "active" ? "⏳" : "⬜"}</span>
              <span className="batch-label">批次 {i + 1}/{batches.length}</span>
              <span className="batch-range">{b.range}</span>
              <span className="batch-status">{b.status === "done" ? "完成" : b.status === "active" ? "处理中..." : "等待"}</span>
            </div>
          ))}
        </div>
        {message && <div className="pmsg">{message}</div>}
      </div>
    );
  }

  // 非批量模式：标准步骤指示器
  const STEPS = [
    { key: "analyze", label: "分析角色与场景", icon: "🔍" },
    { key: "generate", label: "生成剧本", icon: "✍️" },
    { key: "validate", label: "校验结果", icon: "✅" },
  ];
  const currentIdx = STEPS.findIndex((s) => s.key === step);
  const activeIdx = currentIdx >= 0 ? currentIdx : 0;
  const pct = Math.round(((activeIdx + 1) / STEPS.length) * 100);

  return (
    <div className="progress-bar">
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="progress-steps">
        {STEPS.map((s, i) => (
          <div key={s.key} className={`pstep ${i < activeIdx ? "done" : i === activeIdx ? "active" : ""}`}>
            <span className="pstep-dot">{i < activeIdx ? "✓" : s.icon}</span>
            <span className="pstep-label">{s.label}</span>
          </div>
        ))}
      </div>
      {message && <div className="pmsg">{message}</div>}
    </div>
  );
}
