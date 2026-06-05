export const MOCK_MD = `# 🚀 欢迎使用 x-reader 沉浸式阅读器

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

export const MOCK_JSON = `{
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

export const MOCK_LOG = `2026-05-30 18:00:01.234 [INFO] x-reader system booting up...
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
