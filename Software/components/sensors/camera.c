#include "camera.h"
#include "hardware/uart.h"
#include "sensor_data.h"
#include <stdio.h>
#include <stdlib.h>

static const uint UART0_TX_PIN = 0;
static const uint UART0_RX_PIN = 1;
static const uint UART_BAUD = 115200;

static char uart_buf[128];
static int uart_buf_idx = 0;

void camera_init(void) {
  uart_init(uart0, UART_BAUD);
  gpio_set_function(UART0_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(UART0_RX_PIN, GPIO_FUNC_UART);
}

void camera_poll(void) {
  while (uart_is_readable(uart0)) {
    char c = uart_getc(uart0);
    if (c == '\n' || c == '\r') {
      if (uart_buf_idx > 0) {
        uart_buf[uart_buf_idx] = '\0';

        g_sensor_data.camera_value_count = 0;
        char *p = uart_buf;
        char *end;
        while (*p != '\0' && g_sensor_data.camera_value_count < 16) {
          long val = strtol(p, &end, 10);
          if (p == end) {
            break;
          }
          g_sensor_data.camera_values[g_sensor_data.camera_value_count++] =
              (int)val;
          p = end;
        }

        g_sensor_data.camera_updated = true;
        uart_buf_idx = 0;
      }
    } else {
      if (uart_buf_idx < sizeof(uart_buf) - 1) {
        uart_buf[uart_buf_idx++] = c;
      }
    }
  }
}
