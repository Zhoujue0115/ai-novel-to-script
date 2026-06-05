import "./YamlViewer.css";

export default function YamlViewer({ yamlText }) {
  function handleCopy() {
    navigator.clipboard.writeText(yamlText);
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
    return <div className="yaml-viewer empty">等待生成...</div>;
  }

  return (
    <div className="yaml-viewer">
      <div className="yaml-toolbar">
        <h3>YAML 输出</h3>
        <div className="yaml-actions">
          <button onClick={handleCopy}>复制</button>
          <button onClick={handleDownload}>下载 .yaml</button>
        </div>
      </div>
      <pre className="yaml-content"><code>{yamlText}</code></pre>
    </div>
  );
}
