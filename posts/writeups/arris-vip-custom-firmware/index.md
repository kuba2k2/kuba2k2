---
title: Booting custom firmware on Arris TV boxes
description: A semi-persistent method of booting a custom kernel on Motorola/Arris VIP-series TV boxes with KreaTV firmware.
image: cover.webp
date: 2026-08-22
categories:
  - writeups
  - reveng
  - hwhacking
tags:
  - hacking
  - reverse engineering
  - http
  - arris
  - iptv
  - set top box
  - linux
  - hardware
  - firmware
  - uart
  - programming
  - exploit
  - assembly
---

This write-up describes how a simple command injection vulnerability can be used to achieve a semi-persistent method of booting custom firmware - even without a shell available.

*See the repository on GitHub: [kuba2k2/vipboot](https://github.com/kuba2k2/vipboot)*

--8<-- "repo/README.md:introduction"

--8<-- "repo/README.md:writeup"

## Disclaimer

--8<-- "repo/README.md:disclaimer"
