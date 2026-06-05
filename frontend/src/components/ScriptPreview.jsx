import React from "react";
import jsYaml from "js-yaml";
import "./ScriptPreview.css";

const BEAT_LABELS = {
  narration: "旁白",
  dialogue: "对白",
  action: "动作",
  inner_monologue: "独白",
  stage_direction: "提示",
};

export default function ScriptPreview({ yamlText }) {
  if (!yamlText) {
    return <div className="script-preview empty">等待生成...</div>;
  }

  let data;
  try {
    data = jsYaml.load(yamlText);
  } catch {
    return <div className="script-preview empty">YAML 解析失败，无法预览</div>;
  }

  if (!data || !data.scenes) {
    return <div className="script-preview empty">剧本数据不完整</div>;
  }

  return (
    <div className="script-preview">
      <h2>{data.title || "未命名剧本"}</h2>

      {data.characters?.length > 0 && (
        <section className="characters">
          <h3>角色列表</h3>
          <div className="char-grid">
            {data.characters.map((ch) => (
              <div key={ch.id} className="char-card">
                <strong>{ch.name}</strong>
                <span className={`role-tag ${ch.role}`}>{ch.role}</span>
                <p>{ch.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="scenes">
        <h3>剧本内容</h3>
        {data.scenes.map((scene) => (
          <div key={scene.scene_id} className="scene-card">
            <div className="scene-header">
              <span className="scene-id">{scene.scene_id}</span>
              <strong>{scene.title}</strong>
              <span className="scene-location">{scene.location} · {scene.time}</span>
            </div>
            {scene.summary && <p className="scene-summary">{scene.summary}</p>}
            <div className="beats">
              {scene.beats?.map((beat, i) => (
                <div key={i} className={`beat beat-${beat.type}`}>
                  <span className="beat-type">{BEAT_LABELS[beat.type] || beat.type}</span>
                  {beat.character && <span className="beat-char">{beat.character}</span>}
                  <span className="beat-content">{beat.content}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
