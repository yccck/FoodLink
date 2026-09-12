// 让图片等静态资源带上 Vite base（GitHub Pages 子目录部署时正确解析）
export function asset(p) {
  const base = import.meta.env.BASE_URL || '/'
  return base + String(p).replace(/^\/+/, '')
}
