import React from 'react'
import CodeBlock from './CodeBlock'
import DataTable from './DataTable'
import PlotlyChart from './PlotlyChart'
import { UI_TEXT } from '../config/constants'

function StreamView({ data, isProcessing }) {
  const stages = ['intent', 'candidates', 'plan', 'code', 'exec_log', 'result_preview', 'lineage', 'summary']
  const currentStage = data ? stages.find(stage => data[stage]) || 'idle' : 'idle'


  return (
    <div className="stream-view">
      <h2>{UI_TEXT.STREAM_VIEW.TITLE}</h2>
      
      {/* 处理状态指示器 */}
      {isProcessing && (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <span>{UI_TEXT.STREAM_VIEW.PROCESSING}</span>
        </div>
      )}
      

      {/* 无数据时的占位符 */}
      {(!data || Object.keys(data).length === 0) && !isProcessing && (
        <div className="placeholder-content">
          <div className="placeholder-icon">📊</div>
          <h3>等待分析</h3>
          <p>请输入问题开始数据分析，或点击上方的示例问题</p>
        </div>
      )}

      {/* Intent */}
      {data && data.intent && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.INTENT}</h3>
          <div className="intent-tags">
            {data.intent.intent.is_aggregation && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.AGGREGATION}</span>}
            {data.intent.intent.is_groupby && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.GROUPBY}</span>}
            {data.intent.intent.is_trend && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.TREND}</span>}
            {data.intent.intent.is_ranking && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.RANKING}</span>}
            {data.intent.intent.is_growth && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.GROWTH}</span>}
            {data.intent.intent.is_text_analysis && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.TEXT_ANALYSIS}</span>}
            {data.intent.intent.is_price_analysis && <span className="tag">{UI_TEXT.STREAM_VIEW.INTENT_TAGS.PRICE_ANALYSIS}</span>}
          </div>
        </div>
      )}

      {/* Candidates */}
      {data && data.candidates && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.CANDIDATES}</h3>
          {data.candidates.candidates.map((candidate, idx) => (
            <div key={idx} className="candidate-card">
              <div className="candidate-header">
                <span className="candidate-name">
                  {candidate.file_name} - {candidate.sheet_name}
                </span>
                <span className="candidate-score">
                  得分: {candidate.score.toFixed(3)}
                </span>
              </div>
              <div className="candidate-info">
                <span>{candidate.row_count} 行 × {candidate.column_count} 列</span>
              </div>
              <div className="candidate-rationale">
                {candidate.rationale}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Plan - 隐藏 */}
      {/* {data.plan && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.PLAN}</h3>
          <pre className="plan-json">
            {JSON.stringify(data.plan.plan, null, 2)}
          </pre>
        </div>
      )} */}

      {/* Prompt (Debug) */}
      {data && data.prompt && (
        <div className="stream-section debug-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.PROMPT}</h3>
          <details>
            <summary>点击展开查看完整prompt</summary>
            <pre className="prompt-content">
              {data.prompt.prompt}
            </pre>
          </details>
        </div>
      )}

      {/* Code - 折叠显示 */}
      {data && data.code && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.CODE}</h3>
          <details>
            <summary>点击展开查看完整代码</summary>
            <CodeBlock code={data.code.code} language={data.code.language} />
          </details>
        </div>
      )}

      {/* Pseudocode - 伪代码显示 */}
      {data && data.pseudocode && (
        <div className="stream-section">
          <h3>📝 分析流程（伪代码）</h3>
          <div className="pseudocode-content">
            <pre>{(() => {
              // 处理伪代码数据
              let pseudocodeText = '';
              if (typeof data.pseudocode === 'string') {
                pseudocodeText = data.pseudocode;
              } else if (data.pseudocode && typeof data.pseudocode === 'object') {
                // 如果是对象，尝试提取pseudocode字段
                pseudocodeText = data.pseudocode.pseudocode || JSON.stringify(data.pseudocode, null, 2);
              } else {
                pseudocodeText = JSON.stringify(data.pseudocode, null, 2);
              }
              
              // 清理markdown代码块标记
              pseudocodeText = pseudocodeText.replace(/^```[\s\S]*?\n/, '').replace(/\n```$/, '');
              
              return pseudocodeText;
            })()}</pre>
          </div>
        </div>
      )}

      {/* Execution Log */}
      {data && data.exec_log && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.EXEC_LOG}</h3>
          <pre className="exec-log">
            {data.exec_log.message}
          </pre>
        </div>
      )}

      {/* Result Preview */}
      {data && data.result_preview && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.RESULT}</h3>
          
          {/* Figures */}
          {data.result_preview.figures && data.result_preview.figures.length > 0 && (
            <div className="figures-container">
              {data.result_preview.figures.map((fig, idx) => (
                <PlotlyChart key={idx} figure={fig} />
              ))}
            </div>
          )}
          
          {/* Tables */}
          {data.result_preview.tables && data.result_preview.tables.length > 0 && (
            <div className="tables-container">
              {data.result_preview.tables.map((table, idx) => (
                <DataTable key={idx} table={table} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Lineage */}
      {data && data.lineage && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.LINEAGE}</h3>
          <div className="lineage-info">
            <p>
              <strong>使用字段:</strong> {data.lineage.used_columns.join(', ')}
            </p>
            <p>
              <strong>字段数量:</strong> {data.lineage.column_count} / {data.lineage.original_column_count}
            </p>
            <p>
              <strong>覆盖率:</strong> {(data.lineage.coverage * 100).toFixed(1)}%
            </p>
          </div>
          
          {data.lineage.mapping && data.lineage.mapping.length > 0 && (
            <div className="lineage-mapping">
              <h4>字段映射:</h4>
              <table className="mapping-table">
                <thead>
                  <tr>
                    <th>原始字段</th>
                    <th>使用字段</th>
                  </tr>
                </thead>
                <tbody>
                  {data.lineage.mapping.map((m, idx) => (
                    <tr key={idx}>
                      <td>{m.original}</td>
                      <td>{m.used}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {data && data.summary && (
        <div className="stream-section">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.SUMMARY}</h3>
          <div className="summary-content" dangerouslySetInnerHTML={{ __html: data.summary.summary.replace(/\n/g, '<br/>') }} />
        </div>
      )}

      {/* Error */}
      {data && data.error && (
        <div className="stream-section error">
          <h3>{UI_TEXT.STREAM_VIEW.SECTIONS.ERROR}</h3>
          <p>{data.error.message}</p>
          {data.error.stderr && (
            <pre className="error-stderr">{data.error.stderr}</pre>
          )}
        </div>
      )}
    </div>
  )
}

export default StreamView

