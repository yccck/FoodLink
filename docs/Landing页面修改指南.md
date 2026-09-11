# Landing 页面（首页落地页）修改指南

> 目标读者：需要在本地打开并重新布置前端 landing 页面的同学
> 前端技术栈：Vue 3 + Vite，包管理 npm

---

## 一、打开页面（每次开发前）

### 1. 启动前端

VS Code 打开 `E:\FoodLinkRepo`，按 `` Ctrl+` `` 打开终端：

```powershell
cd frontend
npm run dev
```

看到 `Local: http://localhost:5173/` 即成功，浏览器打开 **http://localhost:5173/** 就是 landing 页。

> 依赖已提前装好（node_modules 已存在），以后每次只需 `npm run dev`。
> 如果换电脑或删过 node_modules，先执行一次 `npm install`。

### 2. 热更新

Vite 自带热更新：**改代码 → Ctrl+S 保存 → 浏览器自动刷新**。不需要重启服务。

### 3. 推荐工作布局

VS Code 里 `Ctrl+\` 把编辑器分屏：左边代码、右边再开一个浏览器窗口看效果；或者浏览器按 `F12` 打开开发者工具，用设备模拟看手机端效果。

---

## 二、Landing 页的文件地图（改之前必读）

Landing 页 = 路由 `/`，公开页面（不用登录）。它由 **3 个文件**组成，分工如下：

| 文件 | 作用 | 什么时候改它 |
|---|---|---|
| `src/views/Landing.vue`（110 行） | **页面外壳**：Vue 组件，负责把 HTML 注入页面 + 顶栏滚动动效 + 登录态显示 + 自定义颜色样式 | 改配色、按钮样式、动效、登录/退出逻辑 |
| `src/views/deepseek-home.html`（3 行压缩 HTML） | **页面内容和结构**：所有文案、板块、布局都在这里 | 改文案、增删板块、调整布局 |
| `src/assets/deepseek.css` | 页面基础样式（复刻自 DeepSeek 官网的原生 CSS） | 一般不动；要改样式优先在 Landing.vue 的 `<style>` 里覆盖 |

当前页面是「复刻 DeepSeek 官网」的结构：顶部导航栏（品牌名「食愿」+ 登录态）→ hero 主视觉区（橙色光斑背景 + 入口卡片）→ 各功能介绍板块 → 页脚。

---

## 三、按需求类型选改法

### 场景 A：改文案（标题、介绍文字、按钮文字）

1. VS Code 打开 `src/views/deepseek-home.html`；
2. `Ctrl+F` 搜现有文字（如「食愿」），替换成新文案；
3. 保存，浏览器自动刷新看效果。

> ⚠️ 这个文件是压缩过的（只有 3 行但每行很长），**一定要靠搜索定位**，不要试图通读。建议先在 VS Code 里右键 →「格式化文档」，把它展开成多行后再改，改起来直观得多。

### 场景 B：改配色 / 按钮样式 / 间距

打开 `src/views/Landing.vue`，在**底部 `<style>` 区块**追加或修改 CSS。已有示例：

```css
/* 品牌名颜色（当前深橙 #ea580c） */
.ds-brand-name { color: #ea580c; }

/* hero 区光斑背景 */
.ds-glow-bg { background-image: radial-gradient(...); }
```

想改主色调，就改这里的颜色值；想隐藏某个板块，加 `.ds-xxx { display: none; }`。

> 原则：**覆盖样式写在 Landing.vue，不去动 assets/deepseek.css**，这样原始样式永远可以回退。

### 场景 C：调整板块结构（增删板块、换顺序）

1. 先在 `deepseek-home.html` 里格式化文档；
2. 每个板块是一段 `<section>` 或带 `ds-` 前缀 class 的 `<div>`，整段剪切/复制/删除即可；
3. 保存看效果，样式乱了就在 Landing.vue `<style>` 里补覆盖。

### 场景 D：彻底重做（推荐，如果要大改）

当前的 landing 页是「注入一段压缩 HTML」的临时方案，大改很痛苦。如果要做真正的重新设计，建议**把 Landing.vue 改写成正常的 Vue 组件**：

```
<template> 里写自己的板块结构（导航 / 主视觉 / 功能介绍 / 页脚）
<style scoped> 里写自己的样式
```

不再 import deepseek-home.html 和 deepseek.css。这样每个板块都是清晰的 Vue 代码，队友也好维护。需要的话可以让 AI 直接帮你生成一版。

---

## 四、修改后的检查清单

- [ ] 未登录状态打开 `/`：页面正常显示，顶栏显示登录入口
- [ ] 登录后回到 `/`：顶栏显示「你好，xxx + 退出登录」（这段逻辑在 Landing.vue 的 `ensureHeaderUser`，改结构时**不要删掉 `.ds-header-bar` 这个容器**，否则登录态注入会失效）
- [ ] 点「退出登录」：能正常退出并跳回登录页
- [ ] F12 设备模拟：手机宽度下排版不崩
- [ ] 滚动页面：顶栏「灵动岛」收缩动效正常（依赖 `.ds-header-bar`，同上别删）

## 五、改完如何提交给团队

当前 `E:\FoodLinkRepo` 是纯代码副本（无 git）。确认改好后告诉我，我帮你把修改后的前端文件提交到团队仓库 `yccck/FoodLink`。

---

## 附：常见报错

| 现象 | 解决 |
|---|---|
| `npm run dev` 报「缺少 node_modules」 | 先 `npm install`（慢就加 `--registry=https://registry.npmmirror.com`） |
| 页面白屏 | F12 看 Console 红色报错，多半是 html 结构改坏了（标签没闭合），撤销重改 |
| 改了没反应 | 确认保存了（Ctrl+S）；还不行就终端里 Ctrl+C 停掉再 `npm run dev` |
| 端口被占用 | 终端会提示换到 5174，用新端口打开即可 |
