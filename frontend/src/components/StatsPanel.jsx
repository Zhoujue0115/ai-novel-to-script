import React from "react";
import "./StatsPanel.css";

export default function StatsPanel({ stats }) {
  if (!stats || stats.error) return <div className="stats-panel"><p>暂无统计数据</p></div>;

  return (
    <div className="stats-panel">
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-value">{stats.total_scenes}</span>
          <span className="stat-label">场景数</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.total_beats}</span>
          <span className="stat-label">内容块</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.total_characters}</span>
          <span className="stat-label">角色数</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.dialogue_ratio}%</span>
          <span className="stat-label">对白占比</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.avg_beats_per_scene}</span>
          <span className="stat-label">平均块/场景</span>
        </div>
      </div>

      {stats.beat_distribution?.length > 0 && (
        <div className="stat-section">
          <h4>内容类型分布</h4>
          <div className="bar-chart">
            {stats.beat_distribution.map((b) => {
              const pct = stats.total_beats > 0 ? Math.round(b.value / stats.total_beats * 100) : 0;
              return (
                <div key={b.type} className="bar-row">
                  <span className="bar-label">{b.name}</span>
                  <div className="bar-track"><div className="bar-fill" style={{ width: `${pct}%` }} /></div>
                  <span className="bar-num">{b.value}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {stats.character_lines?.length > 0 && (
        <div className="stat-section">
          <h4>角色台词量</h4>
          <div className="bar-chart">
            {stats.character_lines.slice(0, 8).map((c) => {
              const max = stats.character_lines[0]?.count || 1;
              const pct = Math.round(c.count / max * 100);
              return (
                <div key={c.name} className="bar-row">
                  <span className="bar-label">{c.name}</span>
                  <div className="bar-track"><div className="bar-fill char" style={{ width: `${pct}%` }} /></div>
                  <span className="bar-num">{c.count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
