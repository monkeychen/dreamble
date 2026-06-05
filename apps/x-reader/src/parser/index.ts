import { HtmlParser } from './htmlParser';
import { MarkdownParser } from './markdownParser';
import { JsonParser } from './jsonParser';
import { LogParser } from './logParser';
import { TxtParser } from './txtParser';
import { CodeParser } from './codeParser';

/**
 * 统一多格式分发解析引擎
 */
export class DocumentParser {
  /**
   * 根据文件名后缀，将原始文本解析并渲染为高质感 HTML 内容
   * @param fileName 文件名或文件完整路径
   * @param rawContent 原始文件文本流
   */
  public static parse(fileName: string, rawContent: string): { html: string; type: string } {
    const ext = this.getFileExtension(fileName).toLowerCase();

    switch (ext) {
      case 'html':
      case 'htm':
        return {
          html: HtmlParser.parse(rawContent),
          type: 'html'
        };
      case 'md':
      case 'markdown':
        return {
          html: MarkdownParser.parse(rawContent),
          type: 'markdown'
        };
      case 'json':
        return {
          html: JsonParser.parse(rawContent),
          type: 'json'
        };
      case 'log':
        return {
          html: LogParser.parse(rawContent),
          type: 'log'
        };
      case 'js':
      case 'javascript':
        return {
          html: CodeParser.parse(rawContent, 'javascript'),
          type: 'javascript'
        };
      case 'py':
      case 'python':
        return {
          html: CodeParser.parse(rawContent, 'python'),
          type: 'python'
        };
      case 'java':
        return {
          html: CodeParser.parse(rawContent, 'java'),
          type: 'java'
        };
      case 'xml':
        return {
          html: CodeParser.parse(rawContent, 'xml'),
          type: 'xml'
        };
      case 'yml':
      case 'yaml':
        return {
          html: CodeParser.parse(rawContent, 'yaml'),
          type: 'yaml'
        };
      case 'properties':
        return {
          html: CodeParser.parse(rawContent, 'properties'),
          type: 'properties'
        };
      case 'txt':
      default:
        // 如果无法识别格式，回退到 txt 高质感纯文本排版
        return {
          html: TxtParser.parse(rawContent),
          type: ext === 'txt' ? 'txt' : 'unknown'
        };
    }
  }

  /**
   * 提取文件名后缀
   */
  private static getFileExtension(fileName: string): string {
    const parts = fileName.split('.');
    if (parts.length <= 1) return '';
    return parts.pop() || '';
  }
}
