/**
 * 辅助函数：将 Base64 编码的数据解码为 UTF-8 字符串，防中文乱码
 */
function decodeBase64ToUtf8(b64Data: string): string {
  const b64 = b64Data.includes(',') ? b64Data.split(',')[1] : b64Data;
  const binaryStr = atob(b64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  return new TextDecoder('utf-8').decode(bytes);
}

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
          rawText = decodeBase64ToUtf8(fileContents.data);
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

export interface CachedDocInfo {
  name: string;
  size: number;
  mtime: number;
}

/**
 * 获取沙盒永久缓存中的文档列表
 */
export async function getCachedDocuments(): Promise<CachedDocInfo[]> {
  try {
    // @ts-ignore
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    const { files } = await Filesystem.readdir({
      path: 'cached_docs',
      directory: Directory.Data
    });

    const results: CachedDocInfo[] = [];
    for (const file of files) {
      try {
        const stat = await Filesystem.stat({
          path: `cached_docs/${file.name}`,
          directory: Directory.Data
        });
        results.push({
          name: file.name,
          size: stat.size,
          mtime: stat.mtime
        });
      } catch (e) {
        // 忽略单个文件可能由于异常被删导致的 stat 报错
      }
    }
    // 按照最后修改时间降序排列（最近的排最前）
    return results.sort((a, b) => b.mtime - a.mtime);
  } catch (e) {
    console.log('getCachedDocuments is not supported in browser environment.');
    return [];
  }
}

/**
 * 从沙盒永久缓存中读取指定文档的内容
 */
export async function readCachedDocument(fileName: string): Promise<string> {
  try {
    // @ts-ignore
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    const fileContents = await Filesystem.readFile({
      path: `cached_docs/${fileName}`,
      directory: Directory.Data
    });

    if (typeof fileContents.data === 'string') {
      return decodeBase64ToUtf8(fileContents.data);
    }
    throw new Error('File data is not a valid string.');
  } catch (e: any) {
    console.error('Failed to read cached document:', e);
    throw e;
  }
}

/**
 * 从沙盒永久缓存中删除指定文档
 */
export async function deleteCachedDocument(fileName: string): Promise<boolean> {
  try {
    // @ts-ignore
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    await Filesystem.deleteFile({
      path: `cached_docs/${fileName}`,
      directory: Directory.Data
    });
    return true;
  } catch (e) {
    console.error('Failed to delete cached document:', e);
    return false;
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

