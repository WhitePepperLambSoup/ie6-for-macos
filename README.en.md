# Internet Explorer 6 for macOS

**[简体中文](./README.md)** | **English**

---

To solve the long-standing issue that users on the latest macOS cannot use Microsoft's outstanding Internet Explorer browser, we have fully ported Internet Explorer 6 to macOS.

This is not a web wrapper or an Electron skin. It runs the original 2001 Microsoft `iexplore.exe` and `mshtml.dll` (Trident layout engine) binaries directly on macOS.

## Motivation

For years, macOS has suffered from a major gap in its software ecosystem: even on a maxed-out Mac, users have no way to run Microsoft's classic Internet Explorer 6.0 browser.

Modern browsers like Chrome and Safari casually consume gigabytes of RAM while rendering unnecessary features like Flexbox and CSS Grid. By contrast, IE6—released in 2001—gave the web its distinctive box model, `hasLayout` behavior, ActiveX controls, and classic script error dialogs. To bring that experience to Mac users without requiring a virtual machine, we packaged Microsoft Internet Explorer 6.0 SP1 (from Windows 2000 SP1) into a standalone `Internet Explorer 6.app`.

## Features

- **Original Microsoft Binaries**: Runs genuine `iexplore.exe`, `mshtml.dll` (Trident), `shdocvw.dll`, `browseui.dll`, and `jscript.dll` (JScript 5.6).
- **2004 Dual-Language Start Page**: Includes a built-in 2004-era MSN.com and hao123 start page with a language toggle in the top-right corner.
- **Modern Web Access**: Works with Google Search, Baidu, Wikipedia, Hacker News, CNN Lite, and CERN (the world's first website from 1991). You can also open GitHub or Apple.com—if the layout breaks, it simply means their frontend engineers forgot to test on IE6.
- **Classic Error Pages and Dialogs**: Preserves `res://shdoclc.dll/dnserror.htm` and native script error popups.

## Low-Level Compatibility Fixes

Getting a 2001 browser to browse modern web pages on macOS required tracking down and binary-patching two low-level crashes in the 32-bit runtime DLLs:

### 1. `shell32.dll` Value-as-Pointer Crash Fix (`0x00000104`)

When IE6 loads a page and checks the toolbar "Edit" button state, Microsoft's native `browseui.dll` calls `AssocQueryStringByKeyW(..., pszOut, pcchOut)`. According to the Win32 documentation, the 6th argument `pcchOut` must be a `DWORD*` pointer. However, `browseui.dll` passes the buffer length `0x104` (`MAX_PATH = 260`) directly by value.

Disassembling Microsoft's native `shlwapi.dll` revealed an undocumented check: `if ((ULONG_PTR)pcchOut >> 16 == 0)`, treating any pointer below `0x10000` as a literal value rather than dereferencing it. Wine's `shell32.dll` lacked this workaround and executed `movl (%eax), %edx` on address `0x00000104`, causing an immediate `EXCEPTION_ACCESS_VIOLATION`.

We patched the entry of `IQueryAssociations_fnGetString` in `shell32.dll` with a 26-byte x86 machine-code shim that detects `0 < pcchOut < 0x10000` and redirects it to a valid `DWORD` on the stack.

### 2. `kernelbase.dll` Long URL Heap Overflow Fix (`UrlCombineW`)

In the IE6 era, `INTERNET_MAX_URL_LENGTH` was fixed at `2084` characters. Modern web pages (such as Google and Baidu search results) frequently embed inline `data:image/png;base64,...` URIs exceeding 20 KB. When `mshtml.dll` called `UrlCombineW` on these URIs, an unbounded wide-string copy loop wrote past the `0x1048`-byte (4 KB) heap buffer in `kernelbase.dll` and corrupted the process heap.

We binary-patched `UrlCombineW` in `kernelbase.dll` to expand each of its three internal workspaces from `0x1048` bytes to `0x80000` bytes (512 KB per buffer) and added a `0x7ff00`-byte truncation guard to the copy loop.

## Installation

1. Download `Internet-Explorer-6-macOS.dmg` from the **[Releases](../../releases)** page.
2. Open the DMG and drag `Internet Explorer 6.app` into your `Applications` folder.
3. On first launch, **right-click `Internet Explorer 6.app` and select "Open"** (Rosetta 2 is required on Apple Silicon Macs).

## Notes

- This project is intended for retro-computing preservation and reverse-engineering research. Do not use a 2001 browser engine to log into sensitive accounts or online banking.
- Original Internet Explorer binaries are the property of Microsoft Corporation. The compatibility runtime is based on [Wine](https://www.winehq.org/) (LGPL v2.1+).
