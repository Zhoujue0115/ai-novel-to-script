import React, { useState } from "react";
import Cover from "./components/Cover";
import NovelInput from "./components/NovelInput";
import YamlViewer from "./components/YamlViewer";
import ScriptPreview from "./components/ScriptPreview";
import ProgressBar from "./components/ProgressBar";
import StatsPanel from "./components/StatsPanel";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, textAlign: "center" }}>
          <h2>页面出错了</h2>
          <p style={{ color: "#999" }}>{this.state.error?.message}</p>
          <button onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
            style={{ marginTop: 16, padding: "8px 24px", cursor: "pointer" }}>
            刷新页面
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [showCover, setShowCover] = useState(true);
  const [yamlText, setYamlText] = useState("");
  const [validation, setValidation] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ step: null, message: "", batches: [] });
  const [page, setPage] = useState("tool");

  async function handleGenerateStream({ title, chapters }) {
    setLoading(true);
    setError("");
    setYamlText("");
    setValidation(null);
    setStats(null);
    setProgress({ step: "start", message: "正在连接..." });

    try {
      const res = await fetch("/api/script/generate/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, chapters, style: "screenplay" }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let expectDone = false;
      let finalResult = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: done")) {
            expectDone = true;
            continue;
          }
          if (line.startsWith("data: ")) {
            const payload = line.slice(6);
            if (expectDone) {
              finalResult = JSON.parse(payload);
              expectDone = false;
            } else {
              try {
                const data = JSON.parse(payload);
                if (data.step === "error") {
                  setError(data.msg);
                  setLoading(false);
                  return;
                }
                // 批量进度：更新批次列表
                if (data.step === "batch" && data.total) {
                  setProgress((prev) => {
                    const batches = [];
                    for (let i = 0; i < data.total; i++) {
                      if (i < data.batch - 1) batches.push({ status: "done", range: "" });
                      else if (i === data.batch - 1) batches.push({ status: "active", range: data.msg });
                      else batches.push({ status: "pending", range: "" });
                    }
                    return { step: "batch", message: data.msg, batches };
                  });
                } else {
                  setProgress({ step: data.step, message: data.msg });
                }
              } catch {}
            }
          }
        }
      }

      if (finalResult) {
        setYamlText(finalResult.yaml_text);
        setValidation(finalResult.validation);
        setStats(finalResult.stats);
      }
      // 兜底：如果 SSE 没带回 stats，单独请求
      if (finalResult && !finalResult.stats && finalResult.yaml_text) {
        try {
          const sr = await fetch("/api/script/stats", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ yaml_text: finalResult.yaml_text }) });
          if (sr.ok) setStats(await sr.json());
        } catch {}
      }
      setProgress({ step: "done", message: "生成完成" });
    } catch (e) {
      setError("请求失败: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate({ title, chapters }) {
    const n = chapters.length;
    if (n > 15) {
      // 长文用 SSE
      return handleGenerateStream({ title, chapters });
    }
    // 短文用原接口（更快）
    setLoading(true);
    setError("");
    setYamlText("");
    setValidation(null);
    setStats(null);
    setProgress({ step: "generate", message: "正在生成剧本..." });

    try {
      const { generateScript } = await import("./api");
      const { data } = await generateScript(title, chapters);
      if (!data.success) { setError(data.message); return; }
      setYamlText(data.yaml_text);
      setValidation(data.validation);

      setProgress({ step: "validate", message: "正在校验..." });

      // Fetch stats (body, not query param)
      const statsRes = await fetch("/api/script/stats", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yaml_text: data.yaml_text }),
      });
      if (statsRes.ok) setStats(await statsRes.json());

      setProgress({ step: "done", message: "生成完成" });
    } catch (e) {
      setError("请求失败: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <ErrorBoundary>
    {showCover ? (
      <Cover onEnter={() => setShowCover(false)} />
    ) : (
    <div className="app">
      <nav className="nav-bar">
        <div className="nav-brand">AI 小说转剧本</div>
        <div className="nav-tabs">
          <button className={page === "tool" ? "active" : ""} onClick={() => setPage("tool")}>剧本生成</button>
          <button className={page === "stats" ? "active" : ""} onClick={() => setPage("stats")}>
            统计分析</button>
          <button className={page === "help" ? "active" : ""} onClick={() => setPage("help")}>使用说明</button>
        </div>
      </nav>

      {page === "tool" && (
        <main className="app-main">
          <NovelInput onGenerate={handleGenerate} loading={loading} />
          <div className="center-col">
            {progress.step && <ProgressBar step={progress.step} message={progress.message} batches={progress.batches} />}
            <YamlViewer yamlText={yamlText} validation={validation} />
          </div>
          <ScriptPreview yamlText={yamlText} />
        </main>
      )}

      {page === "stats" && (
        <main className="stats-page">
          <h2>剧本统计分析</h2>
          {stats ? <StatsPanel stats={stats} /> : <p style={{color:"#999",textAlign:"center",padding:40}}>请先生成剧本，再查看统计</p>}
        </main>
      )}

      {page === "help" && (
        <main className="help-page">
          <h2>使用说明</h2>
          <div className="help-grid">
            <div className="help-card">
              <span className="help-icon">📝</span>
              <h4>输入小说</h4>
              <p>点「加载示例」或用「上传 TXT」导入小说文件。小说需 ≥3 章，支持 UTF-8/GBK/UTF-16 编码。超过 50 章时设置生成范围（默认 30 章）。</p>
            </div>
            <div className="help-card">
              <span className="help-icon">🤖</span>
              <h4>AI 生成</h4>
              <p>点击「生成剧本」后，系统自动选择最优策略：≤6 章用 LangChain 三步链，7-15 章基础生成，&gt;15 章滑动窗口批量处理（&gt;25 章额外启用 RAG 检索增强）。</p>
            </div>
            <div className="help-card">
              <span className="help-icon">📊</span>
              <h4>查看结果</h4>
              <p>生成后自动展示统计面板（场景数、对白占比、角色台词排行）和结构化剧本预览，支持复制 YAML 和下载 .yaml 文件。</p>
            </div>
            <div className="help-card">
              <span className="help-icon">📄</span>
              <h4>YAML Schema</h4>
              <p>输出采用 7 层嵌套剧本数据结构（title → characters → scenes → beats），覆盖旁白/对白/动作/独白/提示 5 种内容类型。详见 <code>docs/schema.md</code>。</p>
            </div>
          </div>
        </main>
      )}

      {error && <div className="error-toast">{error}</div>}
    </div>
    )}
    </ErrorBoundary>
  );
}
