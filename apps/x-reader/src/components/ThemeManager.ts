export class ThemeManager {
  static init() {
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
}
