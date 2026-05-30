/**
 * 高性能交互式 JSON 树状图渲染引擎
 */
export class JsonParser {
  /**
   * 将 JSON 字符串解析为带折叠展开功能的精美 HTML
   */
  public static parse(jsonStr: string): string {
    let parsedData: any;
    try {
      // 兼容一些包含前导/尾随空格的 JSON
      parsedData = JSON.parse(jsonStr.trim());
    } catch (e: any) {
      // 如果解析失败，回退到普通文本显示并附带错误提示
      return `
        <div class="json-error">
          <p>⚠️ JSON 格式解析失败，已切换为普通文本视图：</p>
          <pre><code>${this.escapeHtml(jsonStr)}</code></pre>
          <p class="error-detail">${e.message}</p>
        </div>
      `;
    }

    const treeHtml = this.renderValue(parsedData, undefined, true);
    
    // 返回带有一键“展开/折叠”交互控制条的高质感容器
    return `
      <div class="json-viewer-container">
        <div class="json-control-bar">
          <span class="json-meta-info">JSON 数据对象</span>
          <div class="json-actions">
            <button id="btn-json-collapse" class="json-btn">⚡ 全部收起</button>
            <button id="btn-json-expand" class="json-btn">⚡ 全部展开</button>
            <button id="btn-json-copy" class="json-btn">📋 复制 RAW</button>
          </div>
        </div>
        <div class="json-tree-body">
          ${treeHtml}
        </div>
      </div>
    `;
  }

  /**
   * 递归渲染 JSON 的每个值
   */
  private static renderValue(value: any, key?: string, isLast = true): string {
    const keySpan = key !== undefined ? `<span class="json-key">"${this.escapeHtml(key)}"</span>: ` : '';
    const comma = isLast ? '' : '<span class="json-comma">,</span>';

    if (value === null) {
      return `<div class="json-line">${keySpan}<span class="json-value json-null">null</span>${comma}</div>`;
    }

    const type = typeof value;

    if (type === 'boolean') {
      return `<div class="json-line">${keySpan}<span class="json-value json-boolean">${value}</span>${comma}</div>`;
    }

    if (type === 'number') {
      return `<div class="json-line">${keySpan}<span class="json-value json-number">${value}</span>${comma}</div>`;
    }

    if (type === 'string') {
      return `<div class="json-line">${keySpan}<span class="json-value json-string">"${this.escapeHtml(value)}"</span>${comma}</div>`;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return `<div class="json-line">${keySpan}<span class="json-bracket">[ ]</span>${comma}</div>`;
      }
      
      let bodyHtml = '';
      for (let i = 0; i < value.length; i++) {
        bodyHtml += `<div class="json-tree-node">${this.renderValue(value[i], undefined, i === value.length - 1)}</div>`;
      }

      return `
        <details open class="json-details">
          <summary class="json-summary">
            ${keySpan}<span class="json-bracket">[</span> <span class="json-item-count">// ${value.length} items</span>
          </summary>
          <div class="json-collapsible-content">
            ${bodyHtml}
          </div>
          <span class="json-bracket-closing">]</span>${comma}
        </details>
      `;
    }

    if (type === 'object') {
      const keys = Object.keys(value);
      if (keys.length === 0) {
        return `<div class="json-line">${keySpan}<span class="json-bracket">{ }</span>${comma}</div>`;
      }

      let bodyHtml = '';
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        bodyHtml += `<div class="json-tree-node">${this.renderValue(value[k], k, i === keys.length - 1)}</div>`;
      }

      return `
        <details open class="json-details">
          <summary class="json-summary">
            ${keySpan}<span class="json-bracket">{</span> <span class="json-item-count">// ${keys.length} keys</span>
          </summary>
          <div class="json-collapsible-content">
            ${bodyHtml}
          </div>
          <span class="json-bracket-closing">}</span>${comma}
        </details>
      `;
    }

    return `<div class="json-line">${keySpan}<span>${this.escapeHtml(String(value))}</span>${comma}</div>`;
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
