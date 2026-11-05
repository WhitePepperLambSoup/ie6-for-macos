#!/usr/bin/env python3
"""
Binary patches for Wine 32-bit builtin shell32.dll and kernelbase.dll
to support genuine Microsoft Internet Explorer 6.0 SP1 (browseui.dll / mshtml.dll)
on modern web pages (such as Google and Baidu).
"""
import sys

def patch_shell32(path: str) -> None:
    data = bytearray(open(path, "rb").read())
    # IQueryAssociations_fnGetString at VMA 0x10005e98 (file offset 0x5e98):
    # Redirect pcchOut when passed by value (< 0x10000, e.g. MAX_PATH = 0x104 from browseui.dll)
    # to a valid stack DWORD at 0x14(%ebp).
    patch = bytes.fromhex(
        "8b551c"          # movl 0x1c(%ebp), %edx
        "85d2"            # testl %edx, %edx
        "7411"            # je 0x10005eb0
        "f7c20000ffff"    # testl $0xffff0000, %edx
        "7509"            # jne 0x10005eb0
        "895514"          # movl %edx, 0x14(%ebp)
        "8d5514"          # leal 0x14(%ebp), %edx
        "89551c"          # movl %edx, 0x1c(%ebp)
        "eb35"            # jmp 0x10005ee7
    )
    data[0x5e98:0x5e98 + len(patch)] = patch
    open(path, "wb").write(data)

def patch_kernelbase(path: str) -> None:
    data = bytearray(open(path, "rb").read())
    # UrlCombineW (VMA 0x7b046df0): expand internal 3x buffers from 0x1048 bytes (4 KB)
    # to 0x80000 bytes (512 KB each, 0x180000 total) and bound the relative URL copy loop.
    data[0x46ea1:0x46ea6] = bytes.fromhex("6800001800")      # pushl $0x180000
    data[0x46eb3:0x46eb9] = bytes.fromhex("8db000000800")    # leal 0x80000(%eax), %esi
    data[0x46ec9:0x46ed0] = bytes.fromhex("c745cc00000400")  # movl $0x40000, -0x34(%ebp)
    data[0x46f5b:0x46f61] = bytes.fromhex("81c200001000")    # addl $0x100000, %edx

    loop_patch = bytes.fromhex(
        "0fb7140e"        # movzwl (%esi,%ecx), %edx
        "81f900ff0700"    # cmpl $0x7ff00, %ecx
        "7202"            # jb +2
        "31d2"            # xorl %edx, %edx
        "66891408"        # movw %dx, (%eax,%ecx)
        "83c102"          # addl $0x2, %ecx
        "6685d2"          # testw %dx, %dx
        "75e6"            # jne 0x7b046f31
        "0f1f440000"      # nopl (%eax,%eax)
    )
    data[0x46f31:0x46f50] = loop_patch
    open(path, "wb").write(data)

def patch_shdoclc(path: str) -> None:
    data = bytearray(open(path, "rb").read())
    # Resource string 1211 (0x4bb) at file offset 0x77922 (66 UTF-16LE chars):
    # Replace legacy http://auto.search.msn.com/response.asp?MT=%1&srch=%2&prov=%3&utf8
    s1 = "https://www.google.com/search?gbv=1&ie=UTF-8&oe=UTF-8&btnG=Go&q=%1"
    data[0x77922:0x77922 + 132] = s1.encode("utf-16le")
    # Resource string 1214 (0x4be) at file offset 0x77a5c (46 UTF-16LE chars):
    # Replace legacy http://ieautosearch/response.asp?MT=%1&srch=%2
    s2 = "https://www.google.com/search?gbv=1&hl=en&q=%1"
    data[0x77a5c:0x77a5c + 92] = s2.encode("utf-16le")
    open(path, "wb").write(data)

def patch_shdocvw(path: str) -> None:
    data = bytearray(open(path, "rb").read())
    # CURLSearchHook (VA 0x71098423, file offset 0x97823):
    # Treat single-word queries without '.' in the Address Bar as search queries
    # rather than NetBIOS/WINS hostnames.
    patch = bytes.fromhex("6a2e57ff15f01200715685c07475e98b000000")
    data[0x97823:0x97823 + len(patch)] = patch
    open(path, "wb").write(data)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <shell32.dll> <kernelbase.dll> [shdoclc.dll] [shdocvw.dll]")
        sys.exit(1)
    patch_shell32(sys.argv[1])
    patch_kernelbase(sys.argv[2])
    if len(sys.argv) >= 4:
        patch_shdoclc(sys.argv[3])
    if len(sys.argv) >= 5:
        patch_shdocvw(sys.argv[4])
    print("Successfully applied IE6 binary patches")
