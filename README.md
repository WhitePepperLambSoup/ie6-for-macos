# Internet Explorer 6 for macOS

**简体中文** | **[English](./README.en.md)**

---

为了解决广大用户在最新 macOS 上用不到微软优秀的 IE 浏览器的痛点，我们把 Internet Explorer 6 完整移植到了 macOS 上面。

本项目运行的不是网页或 Electron 套壳，而是微软 2001 年原版 `iexplore.exe` 与 `mshtml.dll`（Trident 排版引擎）。

## 为什么要做这个

长期以来，macOS 存在一个明显的生态缺失：哪怕买到最新顶配的 Mac，系统里也用不上微软经典的 Internet Explorer 6.0 浏览器。

现在的 Chrome、Safari 等浏览器动辄占用几个 G 内存，还塞满了 Flexbox、CSS Grid 等花里胡哨的特性。相比之下，2001 年发布的 IE6 拥有独特的盒模型、`hasLayout` 机制、ActiveX 控件以及经典的脚本错误弹窗。为了让 Mac 用户也能用上优秀的 IE6，我们将 Windows 2000 SP1 下的 Microsoft Internet Explorer 6.0 SP1 完整移植并封装成了独立的 `Internet Explorer 6.app`，无需安装虚拟机，双击即可运行。

## 功能特点

- **原版内核**：直接运行微软原版 `iexplore.exe`、`mshtml.dll`（Trident）、`shdocvw.dll`、`browseui.dll` 与 `jscript.dll`（JScript 5.6）。
- **2004 双语起始页**：默认内置 2004 年风格的 MSN.com 与 hao123 网址之家，右上角可直接切换中英文版本。
- **支持访问现代网站**：可直接访问 Google 搜索、百度、维基百科、Hacker News、CNN Lite 以及 CERN（1991 年世界第一个网站）。你也可以用它打开 GitHub 或 Apple 官网——如果页面排版散架了，那说明对方的前端工程师没有做好 IE6 兼容。
- **保留原版错误页与弹窗**：完整保留 `res://shdoclc.dll/dnserror.htm`（找不到服务器页面）和原版脚本报错弹窗。

## 底层兼容性修复

在把 2001 年的 IE6 搬到 macOS 并连接现代网站的过程中，我们通过反汇编定位并修补了两个底层崩溃问题：

### 1. `shell32.dll` 指针传值闪退修复 (`0x00000104`)

当 IE6 打开网页并检查工具栏“编辑”按钮状态时，微软原版 `browseui.dll` 会调用 `AssocQueryStringByKeyW(..., pszOut, pcchOut)`。按文档定义，第 6 个参数 `pcchOut` 应当是一个 `DWORD*` 指针，但当年编写 `browseui.dll` 的微软程序员直接把缓冲区长度 `0x104`（`MAX_PATH = 260`）当成数值传了进去。

反汇编微软原版 `shlwapi.dll` 可以看到，微软在内部做了一个未公开兼容判断：`if ((ULONG_PTR)pcchOut >> 16 == 0)`，即如果发现指针小于 `0x10000`，就当成普通数值处理而不解引用。但 Wine 的 `shell32.dll` 没有这个判断，直接对地址 `0x00000104` 执行 `movl (%eax), %edx`，导致访问网页即触发 `EXCEPTION_ACCESS_VIOLATION` 闪退。

我们在 `shell32.dll` 的 `IQueryAssociations_fnGetString` 入口处打入了一段 26 字节的 x86 机器码补丁，当检测到 `0 < pcchOut < 0x10000` 时自动将其重定向到栈上的有效 `DWORD` 地址。

### 2. `kernelbase.dll` 长 URL 堆溢出修复 (`UrlCombineW`)

IE6 时代规定 `INTERNET_MAX_URL_LENGTH = 2084`，认为 URL 不会超过两千个字符。但现在的网页（如 Google、百度搜索结果页）包含大量超过 20 KB 的内联 `data:image/png;base64,...` 链接。当 `mshtml.dll` 调用 `UrlCombineW` 拼接相对路径时，内部无边界检查的拷贝循环会直接写穿 `kernelbase.dll` 在堆上分配的 `0x1048` 字节（约 4 KB）缓冲区。

我们对 `kernelbase.dll` 的 `UrlCombineW` 进行了二进制修补，将内部三段工作缓冲区从每段 `0x1048` 字节扩容至 `0x80000` 字节（512 KB），并为相对路径拷贝循环加上了 `0x7ff00` 字节的边界截断保护。

## 下载与安装

1. 在 **[Releases](../../releases)** 页面下载 `Internet-Explorer-6-macOS.dmg`。
2. 打开 DMG，将 `Internet Explorer 6.app` 拖入 `Applications`（应用程序）目录。
3. 首次启动时，请**右键点击 `Internet Explorer 6.app` -> 选择“打开”**（Apple Silicon 机型需安装 Rosetta 2）。

## 说明

- 本项目仅供怀旧体验与逆向工程技术交流，请勿使用 2001 年的浏览器内核登录重要账号或网银。
- Internet Explorer 相关原始二进制组件版权归 Microsoft Corporation 所有；内置兼容层基于 [Wine](https://www.winehq.org/)（LGPL v2.1+）。
