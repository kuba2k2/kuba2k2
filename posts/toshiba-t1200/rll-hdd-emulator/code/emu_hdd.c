// Copyright (c) Kuba Szczodrzyński 2025-8-4.

#include "emu_hdd.h"

#include "rll_2of7.pio.h"
#include "st506_data.pio.h"
#include "st506_step.pio.h"

// MFM data
#define PIN_READ		  13
#define PIN_WRITE		  7
// Control Input
#define PIN_SELECT		  2
#define PIN_WRITE_GATE	  3
#define PIN_HEAD_1		  4
#define PIN_DIR_IN		  5
#define PIN_STEP		  6
// Control Output
#define PIN_SEEK_COMPLETE 8
#define PIN_SERVO_GATE	  9
#define PIN_INDEX		  10
#define PIN_TRACK_0		  11
#define PIN_READY		  12

sector_t sector;
uint32_t track_data[HEADS][PULSES_PER_TRACK][CONFIG_WORDS + SECTOR_WORDS * SECTORS_PER_PULSE];
uint track_cur	= TRACK_INVALID;
uint track_next = 0;

void sector_initialize() {
	memset(&sector, 0, sizeof(sector));

#if MODE_V86P
	sector.id_sync	   = 0x62;
	sector.id_marker   = 0xFE;
	sector.data_sync   = 0x62;
	sector.data_marker = 0xF8;
	memset(sector.post_index, 0x33, sizeof(sector.post_index));
	memset(sector.id_preamble, 0xFF, sizeof(sector.id_preamble));
	memset(sector.id_postamble, 0x33, sizeof(sector.id_postamble));
	memset(sector.data_preamble, 0xFF, sizeof(sector.data_preamble));
	memset(sector.data_postamble, 0x33, sizeof(sector.data_postamble));
	memset(sector.inter_record, 0x33, sizeof(sector.inter_record));
#elif MODE_T1200
	sector.id_preamble[0]	 = 0x38;
	sector.id_sync			 = 0xCF;
	sector.id_marker		 = 0x10;
	sector.data_preamble[0]	 = 0x38;
	sector.data_sync		 = 0xCF;
	sector.data_marker		 = 0x02;
	sector.data_postamble[0] = 0x11;
	memset(sector.post_index, 0x33, sizeof(sector.post_index));
	memset(sector.inter_record, 0x33, sizeof(sector.inter_record));
#endif

	sector.pio_padding = 0xAA55AA55;

#if MODE_V86P
	memset(sector.data, 0x6C, sizeof(sector.data));
	sector.data_ecc[0] = 0x57;
	sector.data_ecc[1] = 0xE9;
	sector.data_ecc[2] = 0x9B;
	sector.data_ecc[3] = 0x71;
	sector.data_ecc[4] = 0xCC;
	sector.data_ecc[5] = 0x3C;
#elif MODE_T1200
	memset(sector.data, 0x53, sizeof(sector.data));
	sector.data_ecc[0] = 0xE9;
	sector.data_ecc[1] = 0xF7;
	sector.data_ecc[2] = 0x13;
	sector.data_ecc[3] = 0x02;
	sector.data_ecc[4] = 0x7D;
	sector.data_ecc[5] = 0xF5;
#endif
}

void sector_to_track(PIO pio, uint sm, uint offset, uint16_t cyl, uint8_t hd, uint8_t sec) {
#if MODE_V86P
	sector.cyl_hi = cyl >> 8;
	sector.cyl_lo = cyl & 0xFF;
	sector.hd	  = hd;
	sector.sec	  = sec;
#elif MODE_T1200
	sector.cyl	  = cyl >> 4;
	sector.cyl_hd = ((cyl & 0xF) << 4) | (hd << 1) | (sec & 1);
	sector.sec	  = sec >> 1;
#endif

#if MODE_V86P
	uint16_t crc = calc_crc16(&sector.id_sync, 6, 0x1021, 0xB207 /* 0xE0, 0xF5 */);
#elif MODE_T1200
	uint16_t crc = calc_crc16(&sector.id_sync, 5, 0x8005, 0xCF10 /* 0x22, 0x85 */);
#endif
	sector.id_crc[0] = crc >> 8;
	sector.id_crc[1] = crc & 0xFF;

	if (sec % SECTORS_PER_PULSE == 0) {
		// write config word if sector is right after INDEX/SERVO_GATE pulse
		uint32_t config = sec == 0 ? 0x80000000 : 0;
		// set pulse length
		config |= (INDEX_BITS) << 16;
		// set data length (between consecutive pulses)
		config |= (SECTOR_BITS * SECTORS_PER_PULSE) - 1;
		// words are byte-reversed before going into PIO, so reverse config to compensate for that
		track_data[hd][sec / SECTORS_PER_PULSE][0] = bswap(config);
	}

	uint32_t *data = &track_data[hd][sec / SECTORS_PER_PULSE][CONFIG_WORDS + SECTOR_WORDS * (sec % SECTORS_PER_PULSE)];
	uint8_t *data8 = (void *)data;
	rll_2of7_program_run(
		pio,
		sm,
		offset,
		/* src= */ &sector,
		/* src_words= */ sizeof(sector) / sizeof(uint32_t),
		/* dst= */ data,
		/* dst_words= */ SECTOR_WORDS
	);

#if MODE_V86P
	// replace RLL(2,7) sync word (0x62) with a delayed-clock variant
	// multiply by 2 because of RLL encoding (1 bit -> 2 bits)
	uint32_t sync_pos = ((uint32_t)&sector.id_sync - (uint32_t)&sector) * 2;
	if (data8[sync_pos] == 0b00100000 && data8[sync_pos + 1] == 0b01000100) {
		data8[sync_pos + 1] = 0b00100100;
	}
	// same for data sync
	sync_pos = ((uint32_t)&sector.data_sync - (uint32_t)&sector) * 2;
	if (data8[sync_pos] == 0b00100000 && data8[sync_pos + 1] == 0b01000100) {
		data8[sync_pos + 1] = 0b00100100;
	}
#elif MODE_T1200
	// replace RLL(2,7) sync word (0xCF) with an early-clock variant
	// multiply by 2 because of RLL encoding (1 bit -> 2 bits)
	uint32_t sync_pos = ((uint32_t)&sector.id_sync - (uint32_t)&sector) * 2;
	if (data8[sync_pos] == 0b10000000 && data8[sync_pos + 1] == 0b10001000) {
		data8[sync_pos + 1] = 0b10010000;
	}
	// same for data sync
	sync_pos = ((uint32_t)&sector.data_sync - (uint32_t)&sector) * 2;
	if (data8[sync_pos] == 0b10000000 && data8[sync_pos + 1] == 0b10001000) {
		data8[sync_pos + 1] = 0b10010000;
	}
#endif
}

void load_track(uint rll_2of7_offset, uint track) {
	gpio_put(PIN_SEEK_COMPLETE, false);
	track_next = TRACK_INVALID;

	if (track != 0)
		gpio_put(PIN_TRACK_0, false);

	LT_I("Seeking to track %u", track);
	absolute_time_t start = get_absolute_time();
	for (uint32_t hd = 0; hd < HEADS; hd++) {
		for (uint32_t sec = 0; sec < SECTORS; sec++) {
			if (track != track_cur) {
				// convert a sector of data
				pio_sm_set_enabled(pio1, 0, false);
				sector_to_track(pio0, 0, rll_2of7_offset, track, hd, sec);
				pio_sm_set_enabled(pio1, 0, true);
			} else {
				// seeking not possible - already on the first/last track - do a dummy wait
				sleep_us(10);
			}

			// if a step happens during seeking, return without setting SEEK_COMPLETE
			// but only if the next track is actually different from the one being loaded
			// (this function will be called again with the new track number)
			if (track_next != TRACK_INVALID && track_next != track)
				return;

			// update TRACK_0
			if (track == 0)
				gpio_put(PIN_TRACK_0, true);
		}
	}
	absolute_time_t end = get_absolute_time();
	LT_I("Seek finished in %lld us", absolute_time_diff_us(start, end));

	// update the current track number after a complete seek
	gpio_put(PIN_SEEK_COMPLETE, true);
	track_cur = track;
}

int main(void) {
	stdio_init_all();

	LT_I("RLL-HDD emulator init");

	gpio_init_mask((1 << PIN_SEEK_COMPLETE) | (1 << PIN_TRACK_0) | (1 << PIN_READY));
	gpio_set_dir_out_masked((1 << PIN_SEEK_COMPLETE) | (1 << PIN_TRACK_0) | (1 << PIN_READY));
	gpio_put(PIN_SEEK_COMPLETE, true);
	gpio_put(PIN_TRACK_0, true);
	gpio_put(PIN_READY, true);

	pio_gpio_init(pio1, PIN_READ);
	pio_gpio_init(pio1, PIN_INDEX);
	pio_gpio_init(pio1, PIN_SERVO_GATE);

#if MODE_V86P
	uint rll_2of7_offset = pio_add_program(pio0, &rll_2of7_st_program);
#elif MODE_T1200
	uint rll_2of7_offset = pio_add_program(pio0, &rll_2of7_wd_program);
#endif
	uint st506_data_offset = pio_add_program(pio1, &st506_data_program);
	uint st506_step_offset = pio_add_program(pio1, &st506_step_program);

	sector_initialize();

	// feed the step program with the initial track number
	st506_step_program_init(pio1, 1, st506_step_offset, PIN_STEP, PIN_DIR_IN);
	st506_step_program_start(pio1, 1, &track_next, TRACKS - 1);

	// the data program must have a valid input array at all times
	load_track(rll_2of7_offset, track_next);

	// finally run the data program
	st506_data_program_init(pio1, 0, st506_data_offset, PIN_READ, PIN_SERVO_GATE, 15000000);
	st506_data_program_start(pio1, 0, track_data[0], sizeof(track_data[0]) / sizeof(uint32_t));

	while (1) {
		int ch = stdio_getchar_timeout_us(0);

		while (track_next != TRACK_INVALID) {
			load_track(rll_2of7_offset, track_next);
		}

		switch (ch) {
			case '?': {
				LT_W("Current track: %u", track_cur);
				uint ctrl_chan = st506_data_ctrl_chan[0];
				uint data_chan = st506_data_data_chan[0];
				LT_D("Ctrl chan: %u, Data chan: %u", ctrl_chan, data_chan);
				LT_D("Ctrl busy: %u, Data busy: %u", dma_channel_is_busy(ctrl_chan), dma_channel_is_busy(data_chan));
				LT_D(
					"Ctrl count: %lu, Data count: %lu",
					dma_hw->ch[ctrl_chan].transfer_count,
					dma_hw->ch[data_chan].transfer_count
				);
				LT_D(
					"Ctrl reload: %lu, Data reload: %lu",
					dma_debug_hw->ch[ctrl_chan].dbg_tcr,
					dma_debug_hw->ch[data_chan].dbg_tcr
				);
				LT_D(
					"Ctrl read: 0x%08lx, write: 0x%08lx",
					dma_hw->ch[ctrl_chan].read_addr,
					dma_hw->ch[ctrl_chan].write_addr
				);
				LT_D(
					"Data read: 0x%08lx, write: 0x%08lx",
					dma_hw->ch[data_chan].read_addr,
					dma_hw->ch[data_chan].write_addr
				);
				LT_D("Read addr ptr: %p", st506_data_read_addr);
				LT_D("Read addr: %p", st506_data_read_addr[0]);
				LT_D("Track data ptr: %p", track_data);
				break;
			}

			case '0':
				track_next = 0;
				break;

			case 'X':
				hexdump((void *)&sector, sizeof(sector));
				break;

			case 'x':
				hexdump((void *)track_data[0][0 / SECTORS_PER_PULSE], sizeof(track_data[0][0]));
				break;

			default:
				break;
		}
	}
}
