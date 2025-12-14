---
template: ./template.html
title: Linux Static Binaries
date: 2025-12-11
categories:
  - Tools
---

Linux tools for various architectures, linked statically. Useful for exploring embedded devices, which usually use minimal C runtimes and have limited storage space available.

- Click the "info" icon next to each program to check the version, sources, hashes and other info.
- Some binaries were built using the [Zig Compiler](https://ziglang.org/).
- Many of these binaries were not compiled by me, so I can't guarantee if they're 100% safe. **Use at your own risk.**

**Sources of 3rd-party builds**:

- [Serverless Industries](https://serverless.industries/2023/07/02/static-binaries.en.html) - arch: `aarch64`, `armv7`, `x86`, `x86_64`
- [ryanwoodsmall/static-binaries](https://github.com/ryanwoodsmall/static-binaries) - arch: `aarch64`, `armv7`, `or1k`, `riscv64`, `x86`, `x86_64`
- [guyush1/gdb-static](https://github.com/guyush1/gdb-static) - arch: `aarch64`, `armv7`, `mips`, `mipsel`, `powerpc`, `x86_64`

**Other repositories with static builds** (not included on this page):

- [ab2pentest/linux-static-binaries](https://github.com/ab2pentest/linux-static-binaries) - arch: `x86`, `x86_64` - tiny binaries based on Busybox
- [polaco1782/linux-static-binaries](https://github.com/polaco1782/linux-static-binaries) - arch: `aarch64`, `armv7`, `x86` - almost 1000 different programs
- [static-linux/static-binaries-i386](https://github.com/static-linux/static-binaries-i386) - arch: `x86` - pretty old versions, with sources
