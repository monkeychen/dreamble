import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-properties';
import DOMPurify from 'dompurify';

/**
 * 通用代码文件语法高亮解析器
 */
export class CodeParser {
  public static parse(code: string, language: string): string {
    if (!code || code.trim() === '') {
      return `<div class="txt-empty">📭 这是一个空的代码文件</div>`;
    }

    const grammar = Prism.languages[language];
    let highlighted = code;
    
    if (grammar) {
      highlighted = Prism.highlight(code, grammar, language);
    } else {
      // 回退：简单的防注入转义
      highlighted = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    
    const rawHtml = `
      <div class="code-reader-container" style="padding: 16px; overflow-x: auto; background-color: var(--bg-primary);">
        <pre style="margin: 0;"><code class="language-${language}">${highlighted}</code></pre>
      </div>
    `;

    return DOMPurify.sanitize(rawHtml, {
      ADD_TAGS: ['style', 'pre', 'code'],
      ADD_ATTR: ['class', 'style', 'id'],
    });
  }
}
