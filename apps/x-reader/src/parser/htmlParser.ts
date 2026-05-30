import DOMPurify from 'dompurify';

/**
 * HTML 解析与安全净化器
 */
export class HtmlParser {
  /**
   * 净化 HTML 内容，防止 XSS，同时保留样式与基本的布局类标签
   */
  public static parse(rawHtml: string): string {
    // 配置 DOMPurify 以允许 class 和 style 属性，使得原有的精美排版得以保留
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      WHOLE_DOCUMENT: false, // 我们只需要 body 内的内容或者片段
      ADD_TAGS: ['style', 'link', 'meta'], // 允许内联样式表
      ADD_ATTR: ['class', 'style', 'id', 'align'],
      FORCE_BODY: true,
    });

    return cleanHtml;
  }
}
