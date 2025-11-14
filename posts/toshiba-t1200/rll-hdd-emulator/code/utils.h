// Copyright (c) Kuba Szczodrzyński 2025-8-4.

#pragma once

#include "emu_hdd.h"

void hexdump(const uint8_t *buf, size_t len);
uint16_t calc_crc16(const uint8_t *data, uint32_t len, uint16_t poly, uint16_t crc);

inline uint32_t bswap(uint32_t word) {
	return ((word & 0xFF) << 24) | ((word & 0xFF00) << 8) | ((word & 0xFF0000) >> 8) | ((word & 0xFF000000) >> 24);
}
