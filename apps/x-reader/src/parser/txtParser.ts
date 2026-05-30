/**
 * 纯文本高质感电子书排版解析器
 */
export class TxtParser {
  /**
   * 将纯文本解析为格式优美、带有段落标签的 HTML 结构
   */
  public static parse(txtContent: string): string {
    if (!txtContent || txtContent.trim() === '') {
      return `<div class="txt-empty">📭 这是一个空文件</div>`;
    }

    // 1. 将文本按双换行符或多个换行符切分为自然的段落
    const rawParagraphs = txtContent.split(/\n\s*\n/);
    let htmlParagraphs = '';

    for (const paragraph of rawParagraphs) {
      const trimmed = paragraph.trim();
      if (!trimmed) continue;

      // 2. 将段落内单个孤立的换行符转换为空格或 <br> (处理中英文混合排版)
      // 如果是中文，孤立的换行可以连接起来；如果是英文，换行应替换为空格
      const isChinese = /[\u4e00-\u9fa5]/.test(trimmed);
      let formattedText = '';
      
      if (isChinese) {
        // 中文段落中的单个换行通常是文本编辑器折行，我们直接去掉它以防排版零碎，但保留段首空格缩进
        formattedText = trimmed.replace(/\n/g, '');
      } else {
        // 英文段落中的单个换行，通常是自动折行，替换为空格
        formattedText = trimmed.replace(/\n/g, ' ');
      }

      // 3. 转义特殊字符，并包裹上标准的排版段落类
      const escapedText = this.escapeHtml(formattedText);
      htmlParagraphs += `<p class="txt-p">${escapedText}</p>`;
    }

    return `
      <div class="txt-reader-container">
        <article class="txt-article-body">
          ${htmlParagraphs}
        </article>
      </div>
    `;
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
