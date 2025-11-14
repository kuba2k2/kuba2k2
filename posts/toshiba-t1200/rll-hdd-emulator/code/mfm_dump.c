// Copyright (c) Kuba Szczodrzyński 2025-8-4.

#include "mfm_dump.h"

#include "mfm_dump.pio.h"

#define PIN_READ  2
#define PIN_INDEX 3

#define MFM_BUF_DEPTH 14
#define MFM_BUF_LEN	  (1 << MFM_BUF_DEPTH)
static uint32_t __attribute__((aligned(4096))) mfm_buf[MFM_BUF_LEN];

void run_once(uint offs, int dma_channel) {
	mfm_dump_program_init(pio0, 0, offs, PIN_READ, 100 * 1000 * 1000);

	dma_channel_config c = dma_channel_get_default_config(dma_channel);
	channel_config_set_transfer_data_size(&c, DMA_SIZE_32);
	channel_config_set_read_increment(&c, false);
	channel_config_set_write_increment(&c, true);
	channel_config_set_dreq(&c, pio_get_dreq(pio0, 0, false));
	channel_config_set_ring(&c, true, 0);
	dma_channel_configure(dma_channel, &c, mfm_buf, &pio0->rxf[0], MFM_BUF_LEN, false);

	dma_channel_start(dma_channel);
	pio_sm_set_enabled(pio0, 0, true);
	uart_putc_raw(uart0, 'S');
	while (dma_channel_is_busy(dma_channel)) {
		if (pio_sm_get_rx_fifo_level(pio0, 0))
			break;
	}
	uart_putc_raw(uart0, 'D');
	dma_channel_wait_for_finish_blocking(dma_channel);
	uart_putc_raw(uart0, 'F');
}

int main(void) {
	set_sys_clock_khz(100 * 1000, true);
	stdio_init_all();
	uart_init(uart0, 921600);
	LT_I("MFM dump init");

	gpio_set_function(PIN_READ, GPIO_FUNC_NULL);
	gpio_set_function(PIN_INDEX, GPIO_FUNC_NULL);
	//	gpio_init_mask((1 << PIN_READ) | (1 << PIN_INDEX));
	//	gpio_set_dir_in_masked((1 << PIN_READ) | (1 << PIN_INDEX));
	//	gpio_pull_up(PIN_READ);
	//	gpio_pull_up(PIN_INDEX);

	uint offs = pio_add_program(pio0, &mfm_dump_program);

	memset(mfm_buf, 0, sizeof(mfm_buf));

	int dma_channel = dma_claim_unused_channel(true);
	while (1) {
		char ch = uart_getc(uart0);
		if (dma_channel_is_busy(dma_channel)) {
			LT_W("DMA busy");
		}
		switch (ch) {
			case 's':
				run_once(offs, dma_channel);
				break;

			case 'h':
				hexdump((void *)mfm_buf, 512);
				break;

			case 'i':
				LT_I("/INDEX = %d", gpio_get(PIN_INDEX));
				break;
			case 'r':
				LT_I("+READ = %d", gpio_get(PIN_READ));
				break;

			case 'G': {
				uint8_t params[8];
				for (int i = 0; i < 8; i++) {
					params[i] = uart_getc(uart0);
				}
				uint8_t *buf	= (void *)mfm_buf;
				uint32_t start	= ((uint32_t *)params)[0];
				uint32_t length = ((uint32_t *)params)[1];
				uart_write_blocking(uart0, &buf[start], length);
				break;
			}

			default:
				LT_I("Unknown command");
				break;
		}
	}
}
