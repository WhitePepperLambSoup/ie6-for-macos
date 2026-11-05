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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <path/to/shell32.dll> <path/to/kernelbase.dll>")
        sys.exit(1)
    patch_shell32(sys.argv[1])
    patch_kernelbase(sys.argv[2])
    print("Successfully patched shell32.dll and kernelbase.dll")
