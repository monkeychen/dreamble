import { marked } from 'marked';
import DOMPurify from 'dompurify';
import Prism from 'prismjs';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-markup'; // 支持 HTML/XML

/**
 * Markdown 极速解析器与美化渲染引擎
 */
export class MarkdownParser {
  private static renderer = new marked.Renderer();

  static {
    // 启用 GFM 规范
    marked.setOptions({
      gfm: true,
      breaks: true
    });

    // 针对新版 marked 配置类型安全的自定义代码块渲染器
    MarkdownParser.renderer.code = function({ text, lang }: { text: string; lang?: string }): string {
      const language = lang || 'txt';
      const grammar = Prism.languages[language] || Prism.languages.markup;
      const highlighted = Prism.highlight(text, grammar, language);
      return `<pre><code class="language-${language}">${highlighted}</code></pre>`;
    };
  }

  /**
   * 将 Markdown 文本转换为排版完美的 HTML
   */
  public static parse(mdText: string): string {
    const rawHtml = marked.parse(mdText, { renderer: MarkdownParser.renderer }) as string;
    
    // 安全净化，保留代码块高亮所需要的 class 等
    return DOMPurify.sanitize(rawHtml, {
      ADD_TAGS: ['style'],
      ADD_ATTR: ['class', 'style', 'id'],
    });
  }
}
