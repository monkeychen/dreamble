export async function initCapacitorBridge(onFileReceived: (fileName: string, rawContent: string) => void) {
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
        const decodedPath = decodeURIComponent(data.url);
        const fileName = decodedPath.substring(decodedPath.lastIndexOf('/') + 1);

        // 2. 读取微信临时文件文本流
        const fileContents = await Filesystem.readFile({
          path: data.url
        });

        // 核心中文字符解码机制 (Base64 -> Uint8Array -> UTF-8)
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
        const savedFile = await Filesystem.writeFile({
          path: `cached_docs/${fileName}`,
          data: rawText,
          directory: Directory.Data,
          encoding: Encoding.UTF8,
          recursive: true
        });

        console.log('Document successfully backup in App sandbox:', savedFile.uri);

        // 4. 拉起渲染引擎展示
        onFileReceived(fileName, rawText);

      } catch (err: any) {
        console.error('Failed to receive external file:', err);
        alert(`读取外部文件失败: ${err.message}`);
      }
    });

    // 5. 后台默默执行垃圾清理任务（延迟 5 秒执行，绝不阻塞启动）
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

export async function exitApp() {
  try {
    // @ts-ignore
    const { App } = await import('@capacitor/app');
    App.exitApp();
  } catch (e) {
    console.log('Running in browser context. Cannot exit app.');
    alert('当前处于 Web 预览环境，请使用浏览器的关闭窗口功能。');
  }
}
