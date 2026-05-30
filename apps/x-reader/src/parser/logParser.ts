/**
 * 专为移动端排障优化的日志高性能渲染引擎
 */
export class LogParser {
  /**
   * 将原始日志文本解析为带行号和智能级别高亮的 HTML 结构
   */
  public static parse(logText: string): string {
    const lines = logText.split(/\r?\n/);
    let htmlLines = '';
    
    let infoCount = 0;
    let warnCount = 0;
    let errorCount = 0;
    let debugCount = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.trim() === '' && i === lines.length - 1) continue; // 忽略最后一真空行

      let level = 'info'; // 默认级别
      let lowerLine = line.toLowerCase();

      // 精确的日志级别正则捕获
      if (lowerLine.includes('error') || lowerLine.includes('err') || lowerLine.includes('fatal') || lowerLine.includes('severe')) {
        level = 'error';
        errorCount++;
      } else if (lowerLine.includes('warn') || lowerLine.includes('warning')) {
        level = 'warn';
        warnCount++;
      } else if (lowerLine.includes('debug') || lowerLine.includes('trace')) {
        level = 'debug';
        debugCount++;
      } else {
        infoCount++;
      }

      // 转义 HTML 字符，防止日志中有破坏 DOM 的特殊字符
      const escapedContent = this.escapeHtml(line);
      const highlightedContent = this.highlightKeywords(escapedContent);

      htmlLines += `
        <div class="log-row log-${level}" data-level="${level}">
          <span class="log-num">${i + 1}</span>
          <span class="log-text">${highlightedContent}</span>
        </div>
      `;
    }

    return `
      <div class="log-viewer-container">
        <div class="log-control-bar">
          <div class="log-stats">
            <span class="log-badge badge-total">All: ${lines.length}</span>
            <span class="log-badge badge-error">Error: ${errorCount}</span>
            <span class="log-badge badge-warn">Warn: ${warnCount}</span>
            <span class="log-badge badge-info">Info: ${infoCount}</span>
          </div>
          <div class="log-actions">
            <select id="log-filter-select" class="log-select">
              <option value="all">🔍 显示全部日志</option>
              <option value="error">🚨 仅看 ERROR / FATAL</option>
              <option value="warn">⚠️ 仅看 WARN & ERROR</option>
              <option value="info">ℹ️ 仅看 INFO & ABOVE</option>
            </select>
            <button id="btn-log-copy" class="log-btn">📋 复制</button>
          </div>
        </div>
        <div class="log-grid-body" id="log-body-area">
          ${htmlLines}
        </div>
      </div>
    `;
  }

  /**
   * 针对日志行内的一些通用关键字进行高亮标记
   */
  private static highlightKeywords(content: string): string {
    // 高亮日志级别标志，如 [ERROR] 或 ERROR:
    let result = content.replace(
      /(\[?(?:ERROR|ERR|FATAL|WARN|WARNING|INFO|DEBUG|TRACE)\]?:?)/gi,
      `<span class="log-level-flag log-flag-$1">$1</span>`
    );

    // 高亮日期时间（支持 ISO-8601, YYYY-MM-DD, HH:mm:ss）
    result = result.replace(
      /(\d{4}[-/]\d{2}[-/]\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)/g,
      `<span class="log-timestamp">$1</span>`
    );

    return result;
  }

  /**
   * HTML 字符转义，防御注入
   */
  private static escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
