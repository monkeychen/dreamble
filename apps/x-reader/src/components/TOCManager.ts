export class TOCManager {
  private tocDrawerPanel = document.getElementById('toc-drawer-panel')!;
  private drawerOverlayMask = document.getElementById('drawer-overlay-mask')!;
  private tocLinksContainer = document.getElementById('toc-links-container')!;
  private btnToggleToc = document.getElementById('btn-toggle-toc')!;
  private btnCloseToc = document.getElementById('btn-close-toc')!;
  private onOpenCallback?: () => void;

  constructor(onOpenCallback?: () => void) {
    this.onOpenCallback = onOpenCallback;
    this.initEvents();
  }

  private initEvents() {
    this.btnToggleToc.addEventListener('click', () => this.open());
    this.btnCloseToc.addEventListener('click', () => this.close());
    this.drawerOverlayMask.addEventListener('click', () => this.close());
  }

  open() {
    this.tocDrawerPanel.classList.add('open');
    this.drawerOverlayMask.classList.add('show');
    if (this.onOpenCallback) {
      this.onOpenCallback();
    }
  }

  close() {
    this.tocDrawerPanel.classList.remove('open');
    this.drawerOverlayMask.classList.remove('show');
  }

  generate(docType: string, docRenderBody: HTMLElement) {
    this.tocLinksContainer.innerHTML = '';

    // 只有 html 和 markdown 具备标题层级大纲
    if (docType !== 'html' && docType !== 'markdown') {
      this.tocLinksContainer.innerHTML = `<li class="toc-item toc-h1" style="cursor: default; color: var(--text-secondary);">当前格式不支持生成大纲</li>`;
      return;
    }

    // 提取渲染主体里的标题
    const headings = docRenderBody.querySelectorAll('h1, h2, h3');
    
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
        this.close(); // 滚动后收回抽屉
      });

      this.tocLinksContainer.appendChild(li);
    });
  }
}
