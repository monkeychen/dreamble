import { DocumentParser } from './parser';

// ==========================================================================
// 🎨 内置精致的演示数据 (Mock Data) 用于极速预览与测试
// ==========================================================================
const MOCK_MD = `# 🚀 欢迎使用 x-reader 沉浸式阅读器

本项目旨在开发一款**面向移动端的极简、丝滑**的 HTML 与 Markdown 本地文档沉浸式阅读器，彻底解决微信等社交软件内此类文档无法直接优美预览、第三方打开链路冗长繁琐的痛点。

---

## 🛠️ 核心交互设计原则

1. **用户体验至上 (UX First)**
   * **零思考，极简链路**：用户在微信中点击 “用其他应用打开”，即可一键在 'x-reader' 中渲染出最完美的排版。
   * **系统承担复杂性**：微信环境沙盒限制、中文排版抖动、大文件渲染性能，全部在底层默默解决。
   * **极致的视觉美学**：支持精细的暗黑模式、高阶毛玻璃底座、以及类似 Typora 的高质感排版主题。

2. **渐进式展示 (Progressive Disclosure)**
   * **沉浸化首屏**：打开文档默认 100% 区域为纯净阅读区，无任何杂乱按钮。
   * **轻触唤醒交互**：轻触屏幕中部，优雅滑出顶部面包屑与底部悬浮控制栏；再次轻触则恢复纯净视界。

3. **离线与缓存第一**
   * 自动在本地沙盒存储一份轻量化的缓存备份，防止微信 3-7 天后强制清理聊天文件导致 “下次想看时文件已失效”。

---

## 🧑‍💻 新增多格式文本支持

为了让创作者、程序员在手机上获得最佳的极客体验，我们现在深度支持了：
* **HTML 文件**：100% 完美样式还原，不坍塌。
* **JSON 文件**：高性能 'details' / 'summary' 折叠树，十万行流畅展开。
* **LOG 日志**：ERROR 等级别温和配色，支持 **CSS 级 100x 速度的一键过滤**。
* **TXT 文件**：段落自适应、墨水屏风格高雅排版。

> "把任何重复 3 遍的事 AI 化或自动化。" —— 我们的工作哲学。
`;

const MOCK_JSON = `{
  "appName": "x-reader",
  "version": "1.0.0",
  "author": "Chen Zhian",
  "description": "极简移动端 HTML/Markdown 沉浸式阅读器",
  "features": [
    "微信一键唤醒渲染",
    "独立沙盒防清理永久缓存",
    "Typora 级别高质感排版主题",
    "JSON 交互折叠树",
    "LOG 日志 ERROR 瞬时 CSS 过滤",
    "TXT 高质感电子书段落净化"
  ],
  "engineConfig": {
    "parseMode": "extreme-speed",
    "useVirtualScroll": true,
    "maxLoadBytes": 52428800,
    "themePresets": {
      "github": "classic-white",
      "sspai": "warm-red-orange",
      "wood": "humanities-warm-paper",
      "dark": "low-reflection-gray"
    }
  },
  "isReleased": false,
  "systemRequirements": {
    "iOS": ">= 14.0",
    "Android": ">= 9.0"
  }
}`;

const MOCK_LOG = `2026-05-30 18:00:01.234 [INFO] x-reader system booting up...
2026-05-30 18:00:01.238 [INFO] Loading theme presets: github, sspai, wood, dark.
2026-05-30 18:00:01.240 [DEBUG] Debugger attached. Running local dev server at http://localhost:5173.
2026-05-30 18:00:02.001 [INFO] Registering File Type Associations: .md, .html, .txt, .log, .json.
2026-05-30 18:00:02.105 [WARN] Local filesystem permissions missing. Requesting user permission for sandbox backup...
2026-05-30 18:00:02.110 [INFO] Permission GRANTED by operating system.
2026-05-30 18:00:03.450 [ERROR] Failed to fetch external theme assets from raw.githubusercontent.com: Timeout 5000ms.
2026-05-30 18:00:03.452 [WARN] External asset fetch failed. Falling back to local embedded base themes.
2026-05-30 18:00:03.455 [INFO] Local fallback themes loaded successfully.
2026-05-30 18:00:04.102 [ERROR] WeChat temporary file path check failed: File does not exist. (Code: 404)
2026-05-30 18:00:04.105 [INFO] Initiating automatic retry of WeChat file recovery bridge in 2000ms...
2026-05-30 18:00:06.106 [INFO] Retry SUCCESS. WeChat temporary file found and copied to App secure sandbox: file:///data/user/0/com.chenzhian.xreader/files/welcome_guide.md
2026-05-30 18:00:06.115 [INFO] x-reader core engine activated. Ready for immersive rendering.`;

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

  // 大纲抽屉元素
  private btnToggleToc = document.getElementById('btn-toggle-toc')!;
  private btnCloseToc = document.getElementById('btn-close-toc')!;
  private tocDrawerPanel = document.getElementById('toc-drawer-panel')!;
  private drawerOverlayMask = document.getElementById('drawer-overlay-mask')!;
  private tocLinksContainer = document.getElementById('toc-links-container')!;

  // 状态变量
  private controlsVisible = false;
  private currentFileName = '';
  private currentRawText = '';

  constructor() {
    this.initEvents();
    this.initThemeSwitcher();
    this.initMockButtons();
    this.initCapacitorBridge();
  }

  /**
   * 初始化常规事件监听
   */
  private initEvents() {
    // 1. 沉浸式手势：轻触阅读内容区切换工具栏可见性
    // 点击文档区域触发，但要避开交互式元素（如细节折叠、按钮等）
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      // 如果点击在控制栏、大纲抽屉、或者交互按钮/DETAILS 节点上，不隐藏工具栏
      if (
        this.headerBar.contains(target) ||
        this.floatingDockBar.contains(target) ||
        this.tocDrawerPanel.contains(target) ||
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

    // 4. 大纲抽屉开关逻辑
    this.btnToggleToc.addEventListener('click', () => this.openTOC());
    this.btnCloseToc.addEventListener('click', () => this.closeTOC());
    this.drawerOverlayMask.addEventListener('click', () => this.closeTOC());
  }

  /**
   * 初始化主题切换机制
   */
  private initThemeSwitcher() {
    const indicators = document.querySelectorAll('.theme-indicator');
    
    indicators.forEach((indicator) => {
      indicator.addEventListener('click', () => {
        const theme = indicator.getAttribute('data-theme') || 'github';
        
        // 移除所有已有主题类，注入新主题
        document.body.className = '';
        document.body.classList.add(`theme-${theme}`);
        
        // 可选：将主题设置持久化记录在 LocalStorage 中
        localStorage.setItem('x-reader-theme', theme);
      });
    });

    // 加载历史记录中的主题
    const savedTheme = localStorage.getItem('x-reader-theme');
    if (savedTheme) {
      document.body.className = '';
      document.body.classList.add(`theme-${savedTheme}`);
    }
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
   * 🏆 核心：初始化 Capacitor 跨平台文件接收与沙盒持久化 Bridge
   */
  private async initCapacitorBridge() {
    try {
      // 动态导入 Capacitor 核心与 App 插件，防在纯浏览器中因找不到模块而崩溃
      // @ts-ignore
      const { App } = await import('@capacitor/app');
      // @ts-ignore
      const { Filesystem, Directory, Encoding } = await import('@capacitor/filesystem');

      // 监听外部应用（如微信）点击“用其他应用打开”传入的 URL
      App.addListener('appUrlOpen', async (data: { url: string }) => {
        try {
          if (!data.url) return;

          // 1. 获取微信临时沙盒文件路径
          // data.url 格式通常是: file:///private/var/mobile/Containers/Data/Application/.../tmp/document.md
          const decodedPath = decodeURIComponent(data.url);
          const fileName = decodedPath.substring(decodedPath.lastIndexOf('/') + 1);

          // 2. 读取微信临时文件文本流
          const fileContents = await Filesystem.readFile({
            path: data.url
          });

          // 核心中文字符解码机制 (Base64 -> Uint8Array -> UTF-8)
          // 解决纯 atob() 破坏中文 Unicode 导致乱码的致命问题
          let rawText = '';
          if (typeof fileContents.data === 'string') {
            const b64 = fileContents.data.includes(',') ? fileContents.data.split(',')[1] : fileContents.data;
            const binaryStr = atob(b64);
            const bytes = new Uint8Array(binaryStr.length);
            for (let i = 0; i < binaryStr.length; i++) {
              bytes[i] = binaryStr.charCodeAt(i);
            }
            rawText = new TextDecoder('utf-8').decode(bytes);
          }

          if (!rawText) {
            alert('⚠️ 无法解析该文件内容，请确认文件是否为纯文本或 HTML。');
            return;
          }

          // 3. ⭐️ 核心防失效机制：将临时文件安全地复制到 App 独立的沙盒永久目录中
          // 使用 Directory.Data (App沙盒) 代替 Directory.Documents (公共目录)，彻底免去存储权限弹窗，且安全防清理
          const savedFile = await Filesystem.writeFile({
            path: `cached_docs/${fileName}`,
            data: rawText,
            directory: Directory.Data,
            encoding: Encoding.UTF8,
            recursive: true
          });

          console.log('Document successfully backup in App sandbox:', savedFile.uri);

          // 4. 拉起渲染引擎展示
          this.loadDocument(fileName, rawText);

        } catch (err: any) {
          console.error('Failed to receive external file:', err);
          alert(`读取外部文件失败: ${err.message}`);
        }
      });

      // 5. 后台默默执行垃圾清理任务（延迟 5 秒执行，绝不阻塞启动）
      // 清理超过 14 天的沙盒阅读缓存，防止长年累月产生过多垃圾文件
      setTimeout(async () => {
        try {
          const { files } = await Filesystem.readdir({
            path: 'cached_docs',
            directory: Directory.Data
          });
          
          const now = Date.now();
          const MAX_AGE = 14 * 24 * 60 * 60 * 1000; // 14 天有效期
          
          for (const file of files) {
            try {
              const stat = await Filesystem.stat({
                path: `cached_docs/${file.name}`,
                directory: Directory.Data
              });
              if (now - stat.mtime > MAX_AGE) {
                await Filesystem.deleteFile({
                  path: `cached_docs/${file.name}`,
                  directory: Directory.Data
                });
                console.log(`[Auto Cleanup] 自动清理过期沙盒缓存: ${file.name}`);
              }
            } catch (e) { /* ignore single file stat/delete errors */ }
          }
        } catch (e) {
          // 如果 cached_docs 目录尚未创建，这里会报错，属于正常情况安全忽略
        }
      }, 5000);

    } catch (e) {
      console.log('Running in browser context. Capacitor Native Bridge skipped.');
    }
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
    this.generateTOC(parseResult.type);

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
    this.closeTOC();
    this.fileSelector.value = ''; // 重置文件选择器
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
   * 自动大纲抽取算法 (TOC Generator)
   */
  private generateTOC(docType: string) {
    this.tocLinksContainer.innerHTML = '';

    // 只有 html 和 markdown 具备标题层级大纲
    if (docType !== 'html' && docType !== 'markdown') {
      this.tocLinksContainer.innerHTML = `<li class="toc-item toc-h1" style="cursor: default; color: var(--text-secondary);">当前格式不支持生成大纲</li>`;
      return;
    }

    // 提取渲染主体里的标题
    const headings = this.docRenderBody.querySelectorAll('h1, h2, h3');
    
    if (headings.length === 0) {
      this.tocLinksContainer.innerHTML = `<li class="toc-item toc-h1" style="cursor: default; color: var(--text-secondary);">未检测到标题层级</li>`;
      return;
    }

    headings.forEach((heading, index) => {
      const text = heading.textContent || '';
      const tag = heading.tagName.toLowerCase(); // h1, h2, h3
      
      // 给标题元素打上锚点 ID
      const anchorId = `toc-anchor-${tag}-${index}`;
      heading.setAttribute('id', anchorId);

      // 创建大纲侧边列表项
      const li = document.createElement('li');
      li.className = `toc-item toc-${tag}`;
      li.textContent = text;
      
      li.addEventListener('click', () => {
        // 点击大纲平滑滚动到页面相应位置
        heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
        this.closeTOC(); // 滚动后收回抽屉
      });

      this.tocLinksContainer.appendChild(li);
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
    this.floatingDockBar.classList.remove('remove'); // 兼容
    this.floatingDockBar.classList.remove('show');
    this.controlsVisible = false;
  }

  private openTOC() {
    this.tocDrawerPanel.classList.add('open');
    this.drawerOverlayMask.classList.add('show');
    this.hideControls(); // 打开抽屉时隐藏底层工具栏，避免视觉冲突
  }

  private closeTOC() {
    this.tocDrawerPanel.classList.remove('open');
    this.drawerOverlayMask.classList.remove('show');
  }
}

// ==========================================================================
// 初始化启动
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  new XReaderApp();
});
