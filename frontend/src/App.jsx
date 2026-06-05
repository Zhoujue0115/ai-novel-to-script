import React, { useState } from "react";
import Cover from "./components/Cover";
import NovelInput from "./components/NovelInput";
import YamlViewer from "./components/YamlViewer";
import ScriptPreview from "./components/ScriptPreview";
import { generateScript } from "./api";

export default function App() {
  const [showCover, setShowCover] = useState(true);
  const [yamlText, setYamlText] = useState("");
  const [validation, setValidation] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleGenerate({ title, chapters }) {
    setLoading(true);
    setError("");
    setSuccess("");
    setYamlText("");
    setValidation(null);

    try {
      const { data } = await generateScript(title, chapters);
      if (!data.success) {
        setError(data.message || "生成失败");
        return;
      }
      setYamlText(data.yaml_text);
      setValidation(data.validation);
      if (data.validation?.valid) {
        setSuccess("剧本生成成功，校验通过");
      }
      if (!data.validation?.valid) {
        setError("校验警告: " + data.validation.errors.join(", "));
      }
    } catch (e) {
      setError("请求失败: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  }

  if (showCover) {
    return <Cover onEnter={() => setShowCover(false)} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI 小说转剧本工具</h1>
        <span>将小说章节转为结构化 YAML 剧本</span>
      </header>

      <main className="app-main">
        <NovelInput onGenerate={handleGenerate} loading={loading} />
        <YamlViewer yamlText={yamlText} validation={validation} />
        <ScriptPreview yamlText={yamlText} />
      </main>

      {error && <div className="error-toast">{error}</div>}
      {success && <div className="success-toast">{success}</div>}
    </div>
  );
}
