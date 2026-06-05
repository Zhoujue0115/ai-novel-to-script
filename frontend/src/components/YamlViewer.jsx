import React, { useState } from "react";
import "./YamlViewer.css";

export default function YamlViewer({ yamlText, validation }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(yamlText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([yamlText], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "script.yaml";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!yamlText) {
    return (
      <div className="yaml-viewer empty">
        <div className="empty-icon">---</div>
        <span>等待生成...</span>
      </div>
    );
  }

  const lines = yamlText.split("\n");
  const isValid = validation?.valid;
  const errorCount = validation?.errors?.length || 0;

  return (
    <div className="yaml-viewer">
      <div className="yaml-toolbar">
        <div style={{ display: "flex", alignItems: "center" }}>
          <h3>YAML 输出</h3>
          {validation && (
            <span className={`yaml-status ${isValid ? "pass" : "fail"}`}>
              {isValid ? "校验通过" : `${errorCount} 个问题`}
            </span>
          )}
        </div>
        <div className="yaml-actions">
          <button onClick={handleCopy}>{copied ? "已复制" : "复制"}</button>
          <button onClick={handleDownload}>下载 .yaml</button>
        </div>
      </div>
      <div className="yaml-body">
        <div className="yaml-lines">
          {lines.map((_, i) => (
            <span key={i} className="yaml-ln">{i + 1}</span>
          ))}
        </div>
        <pre className="yaml-content"><code>{yamlText}</code></pre>
      </div>
    </div>
  );
}
