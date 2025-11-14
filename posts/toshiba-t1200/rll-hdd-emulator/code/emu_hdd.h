// Copyright (c) Kuba Szczodrzyński 2025-8-4.

#pragma once

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <hardware/dma.h>
#include <hardware/pio.h>
#include <pico/multicore.h>
#include <pico/stdlib.h>
#include <pico/time.h>

#include <lt_logger.h>

#include "config.h"
#include "utils.h"

#define INDEX_BITS		  805
#define SECTOR_BITS		  9792
#define SECTORS_PER_PULSE 2
#define PULSES_PER_TRACK  17
#define SECTORS			  (SECTORS_PER_PULSE * PULSES_PER_TRACK)
#define HEADS			  2
#define TRACKS			  615

#define CONFIG_WORDS (1)
#define SECTOR_WORDS (SECTOR_BITS / 32)
#define TRACK_WORDS	 ((CONFIG_WORDS + SECTOR_WORDS * SECTORS_PER_PULSE) * PULSES_PER_TRACK)

#define TRACK_INVALID 1024

// #define MODE_V86P 1
#define MODE_T1200 1

typedef struct __attribute__((packed)) {
	uint8_t post_index[24];

	uint8_t id_preamble[15];
	uint8_t id_sync;
	uint8_t id_marker;
#if MODE_V86P
	uint8_t cyl_hi;
	uint8_t cyl_lo;
	uint8_t hd;
	uint8_t sec;
	uint8_t id_crc[2];
	uint8_t id_postamble[3];
#elif MODE_T1200
	uint8_t cyl;
	uint8_t cyl_hd;
	uint8_t sec;
	uint8_t id_crc[2];
	uint8_t id_postamble[4];
#endif

	uint8_t data_preamble[15];
	uint8_t data_sync;
	uint8_t data_marker;
	uint8_t data[512];
	uint8_t data_ecc[6];
#if MODE_V86P
	uint8_t data_postamble[3];
	uint8_t inter_record[24];
#elif MODE_T1200
	uint8_t data_postamble[4];
	uint8_t inter_record[23];
#endif

	uint32_t pio_padding;
} sector_t;
