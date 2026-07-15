import { DocumentParser } from './parser';
import { MOCK_MD, MOCK_JSON, MOCK_LOG } from './components/MockData';
import { ThemeManager } from './components/ThemeManager';
import { TOCManager } from './components/TOCManager';
import { initCapacitorBridge, exitApp, getCachedDocuments, readCachedDocument, deleteCachedDocument } from './components/CapacitorBridge';


// ==========================================================================
// 🚀 核心应用程序管理器
// ==========================================================================
class XReaderApp {
  // DOM 元素引用
  private welcomeArea = document.getElementById('welcome-area')!;
  private docRenderBody = document.getElementById('doc-render-body')!;
  private headerBar = document.getElementById('header-bar')!;
  private floatingDockBar = document.getElementById('floating-dock-bar')!;
  private docNameSpan = document.getElementById('header-doc-name')!;
  private docIconSpan = document.getElementById('header-doc-icon')!;
  private fileSelector = document.getElementById('file-selector') as HTMLInputElement;

  private historyPanel = document.getElementById('history-panel')!;
  private historyList = document.getElementById('history-list')!;

  // 状态变量
  private controlsVisible = false;
  private currentFileName = '';
  private currentRawText = '';
  
  // 组件
  private tocManager: TOCManager;

  constructor() {
    ThemeManager.init();
    this.tocManager = new TOCManager(() => this.hideControls());
    
    this.initEvents();
    this.initMockButtons();
    initCapacitorBridge((fileName, rawContent) => {
      this.loadDocument(fileName, rawContent);
      this.updateHistoryList();
    });
    this.updateHistoryList();
  }

  /**
   * 初始化常规事件监听
   */
  private initEvents() {
    // 1. 沉浸式手势：轻触阅读内容区切换工具栏可见性
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      // 如果点击在控制栏、大纲抽屉、或者交互按钮/DETAILS 节点上，不隐藏工具栏
      if (
        this.headerBar.contains(target) ||
        this.floatingDockBar.contains(target) ||
        target.closest('#toc-drawer-panel') ||
        target.closest('.json-details') ||
        target.closest('.json-actions') ||
        target.closest('.log-control-bar') ||
        target.closest('.welcome-screen') ||
        target.classList.contains('welcome-btn') ||
        target.tagName === 'BUTTON' ||
        target.tagName === 'A' ||
        target.tagName === 'SELECT' ||
        target.tagName === 'OPTION'
      ) {
        return;
      }
      
      this.toggleControls();
    });

    // 2. 关闭当前文档，退回欢迎屏幕
    document.getElementById('btn-close-doc')!.addEventListener('click', () => {
      this.closeDocument();
    });

    // 3. 选择本地文件加载
    this.fileSelector.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        const file = target.files[0];
        const reader = new FileReader();
        reader.onload = (evt) => {
          if (evt.target?.result) {
            this.loadDocument(file.name, evt.target.result as string);
          }
        };
        reader.readAsText(file);
      }
    });

    // 4. 退出应用
    document.getElementById('btn-exit-app')?.addEventListener('click', () => {
      exitApp();
    });
  }

  /**
   * 绑定示例演示按钮
   */
  private initMockButtons() {
    document.getElementById('btn-mock-md')!.addEventListener('click', () => {
      this.loadDocument('welcome_guide.md', MOCK_MD);
    });

    document.getElementById('btn-mock-json')!.addEventListener('click', () => {
      this.loadDocument('config_preset.json', MOCK_JSON);
    });

    document.getElementById('btn-mock-log')!.addEventListener('click', () => {
      this.loadDocument('system_boot.log', MOCK_LOG);
    });
  }

  /**
   * 加载文档到主渲染区
   */
  private loadDocument(fileName: string, rawContent: string) {
    this.currentFileName = fileName;
    this.currentRawText = rawContent;

    // 1. 隐藏欢迎页面
    this.welcomeArea.style.display = 'none';

    // 2. 调用核心多格式解析分流引擎
    const parseResult = DocumentParser.parse(fileName, rawContent);
    this.docRenderBody.innerHTML = parseResult.html;

    // 3. 动态配置图标与头部元信息
    this.docNameSpan.textContent = fileName;
    this.docIconSpan.textContent = this.getFileIcon(parseResult.type);

    // 4. 唤醒并更新专属交互逻辑
    if (parseResult.type === 'json') {
      this.bindJsonEvents();
    } else if (parseResult.type === 'log') {
      this.bindLogEvents();
    }

    // 5. 自动解析生成 TOC 大纲
    this.tocManager.generate(parseResult.type, this.docRenderBody);

    // 6. 默认进入全屏沉浸阅读，隐藏全部控制条
    this.hideControls();
  }

  /**
   * 退出文档，清空渲染区并显示欢迎画面
   */
  private closeDocument() {
    this.docRenderBody.innerHTML = '';
    this.welcomeArea.style.display = 'flex';
    this.currentFileName = '';
    this.currentRawText = '';
    this.docNameSpan.textContent = '未加载文件';
    this.docIconSpan.textContent = '📄';
    this.hideControls();
    this.tocManager.close();
    this.fileSelector.value = ''; // 重置文件选择器
    this.updateHistoryList(); // 返回欢迎屏时，刷新历史记录
  }

  /**
   * 从沙盒中读取永久备份的文档并更新主页面列表
   */
  private async updateHistoryList() {
    const cachedDocs = await getCachedDocuments();
    if (cachedDocs && cachedDocs.length > 0) {
      this.historyPanel.style.display = 'block';
      this.historyList.innerHTML = '';
      
      cachedDocs.forEach((doc) => {
        const item = document.createElement('div');
        item.className = 'history-item';
        
        const timeStr = new Date(doc.mtime).toLocaleDateString('zh-CN', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
        const sizeStr = doc.size > 1024 * 1024 
          ? `${(doc.size / (1024 * 1024)).toFixed(1)} MB` 
          : `${(doc.size / 1024).toFixed(1)} KB`;
        
        item.innerHTML = `
          <div class="history-item-info">
            <span class="history-item-name">${doc.name}</span>
            <div class="history-item-meta">
              <span>🕒 ${timeStr}</span>
              <span>💾 ${sizeStr}</span>
            </div>
          </div>
          <button class="history-delete-btn" title="删除备份">✕</button>
        `;
        
        // 点击卡片本身：读取并载入文档
        item.addEventListener('click', async (e) => {
          const target = e.target as HTMLElement;
          if (target.classList.contains('history-delete-btn')) {
            return;
          }
          
          try {
            const rawContent = await readCachedDocument(doc.name);
            this.loadDocument(doc.name, rawContent);
          } catch (err: any) {
            alert(`无法读取缓存文件: ${err.message}`);
          }
        });
        
        // 点击删除按钮
        item.querySelector('.history-delete-btn')!.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (confirm(`确定要彻底删除该文档的本地备份吗？\n${doc.name}`)) {
            const success = await deleteCachedDocument(doc.name);
            if (success) {
              this.updateHistoryList();
            } else {
              alert('删除失败，请稍后重试。');
            }
          }
        });
        
        this.historyList.appendChild(item);
      });
    } else {
      this.historyPanel.style.display = 'none';
      this.historyList.innerHTML = '';
    }
  }

  /**
   * 绑定 JSON 视图专属交互按钮
   */
  private bindJsonEvents() {
    const container = this.docRenderBody.querySelector('.json-viewer-container');
    if (!container) return;

    // 1. 全部收折
    container.querySelector('#btn-json-collapse')?.addEventListener('click', () => {
      const details = container.querySelectorAll('.json-details');
      details.forEach((d) => (d as HTMLDetailsElement).open = false);
    });

    // 2. 全部展开
    container.querySelector('#btn-json-expand')?.addEventListener('click', () => {
      const details = container.querySelectorAll('.json-details');
      details.forEach((d) => (d as HTMLDetailsElement).open = true);
    });

    // 3. 复制原始 RAW JSON
    container.querySelector('#btn-json-copy')?.addEventListener('click', () => {
      navigator.clipboard.writeText(this.currentRawText)
        .then(() => alert('📋 RAW JSON 复制成功！'))
        .catch(() => alert('📋 复制失败，请手动选择。'));
    });
  }

  /**
   * 绑定 LOG 视图专属高性能 CSS 过滤事件
   */
  private bindLogEvents() {
    const container = this.docRenderBody.querySelector('.log-viewer-container');
    const logBody = container?.querySelector('#log-body-area');
    const filterSelect = container?.querySelector('#log-filter-select') as HTMLSelectElement;
    if (!container || !logBody || !filterSelect) return;

    // 监听过滤器下拉选择
    filterSelect.addEventListener('change', () => {
      const val = filterSelect.value;
      
      // 💡 100x 速度降维打击：通过移除/追加父容器 class 类，完全依赖浏览器原生 CSS 绘制引擎进行隐藏
      logBody.className = 'log-grid-body'; // 重置
      
      if (val === 'error') {
        logBody.classList.add('filter-error');
      } else if (val === 'warn') {
        logBody.classList.add('filter-warn');
      } else if (val === 'info') {
        logBody.classList.add('filter-info');
      }
    });

    // 复制日志内容
    container.querySelector('#btn-log-copy')?.addEventListener('click', () => {
      navigator.clipboard.writeText(this.currentRawText)
        .then(() => alert('📋 日志全文复制成功！'))
        .catch(() => alert('📋 复制失败。'));
    });
  }

  /**
   * 获取格式图标
   */
  private getFileIcon(type: string): string {
    switch (type) {
      case 'html': return '🌐';
      case 'markdown': return '📝';
      case 'json': return '⚙️';
      case 'log': return '🚨';
      case 'txt': return '📖';
      case 'javascript': return '📜';
      case 'python': return '🐍';
      case 'java': return '☕';
      case 'xml': return '🔖';
      case 'yaml': return '⚙️';
      case 'properties': return '🔧';
      default: return '📄';
    }
  }

  // ==========================================================================
  // 🧭 工具栏与抽屉隐藏显示核心动效逻辑
  // ==========================================================================
  private toggleControls() {
    if (this.currentFileName === '') return; // 未加载文件不触发
    
    if (this.controlsVisible) {
      this.hideControls();
    } else {
      this.showControls();
    }
  }

  private showControls() {
    this.headerBar.classList.add('show');
    this.floatingDockBar.classList.add('show');
    this.controlsVisible = true;
  }

  private hideControls() {
    this.headerBar.classList.remove('show');
    this.floatingDockBar.classList.remove('show');
    this.controlsVisible = false;
  }
}

// ==========================================================================
// 初始化启动
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  new XReaderApp();
});
