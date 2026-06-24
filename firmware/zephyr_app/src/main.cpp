#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace {

struct SequenceEvent {
    uint32_t t_us;
    const char* channel;
    int value;
};

constexpr SequenceEvent kSpinEchoDemo[] = {
    {0U, "rf", 1},
    {90U, "rf", 0},
    {120U, "gradient_x", 1},
    {220U, "gradient_x", 0},
    {400U, "adc_gate", 1},
    {800U, "adc_gate", 0},
};

constexpr size_t kCommandBufferSize = 96U;
constexpr size_t kLineBufferSize = 192U;
constexpr size_t kSpinEchoDemoEventCount = sizeof(kSpinEchoDemo) / sizeof(kSpinEchoDemo[0]);

bool g_sequence_running = false;
uint32_t g_sequence_runs = 0U;

struct UartPort {
    const struct device* device;
    const char* name;
    char command[kCommandBufferSize];
    size_t command_length;
    bool line_ready;
    bool overflow;
};

UartPort g_ports[] = {
#if DT_NODE_HAS_STATUS(DT_NODELABEL(usart1), okay)
    {DEVICE_DT_GET(DT_NODELABEL(usart1)), "usart1", {}, 0U, false, false},
#endif
#if DT_NODE_HAS_STATUS(DT_NODELABEL(usart2), okay)
    {DEVICE_DT_GET(DT_NODELABEL(usart2)), "usart2", {}, 0U, false, false},
#endif
#if DT_NODE_HAS_STATUS(DT_NODELABEL(usart3), okay)
    {DEVICE_DT_GET(DT_NODELABEL(usart3)), "usart3", {}, 0U, false, false},
#endif
#if DT_NODE_HAS_STATUS(DT_NODELABEL(usart6), okay)
    {DEVICE_DT_GET(DT_NODELABEL(usart6)), "usart6", {}, 0U, false, false},
#endif
};

void write_string(const struct device* uart, const char* text) {
    for (const char* cursor = text; *cursor != '\0'; ++cursor) {
        uart_poll_out(uart, static_cast<unsigned char>(*cursor));
    }
}

void broadcast(const char* text) {
    for (size_t index = 0; index < sizeof(g_ports) / sizeof(g_ports[0]); ++index) {
        if (device_is_ready(g_ports[index].device)) {
            write_string(g_ports[index].device, text);
        }
    }
}

void broadcast_line(const char* text) {
    broadcast(text);
    broadcast("\r\n");
}

void print_help() {
    broadcast_line("commands:");
    broadcast_line("  HELP      - show command list");
    broadcast_line("  PING      - check serial link");
    broadcast_line("  STATUS    - print controller state");
    broadcast_line("  RUN DEMO  - play built-in spin echo demo");
}

void print_status() {
    char line[kLineBufferSize];
    snprintk(
        line,
        sizeof(line),
        "status state=%s sequence=spin_echo_demo events=%u runs=%u uptime_ms=%lld\n",
        g_sequence_running ? "running" : "idle",
        static_cast<unsigned int>(kSpinEchoDemoEventCount),
        static_cast<unsigned int>(g_sequence_runs),
        static_cast<long long>(k_uptime_get()));
    broadcast(line);
}

void play_spin_echo_demo() {
    if (g_sequence_running) {
        broadcast_line("error sequence_already_running");
        return;
    }

    char line[kLineBufferSize];
    g_sequence_running = true;
    snprintk(line, sizeof(line), "seq_start name=spin_echo_demo events=%u", static_cast<unsigned int>(kSpinEchoDemoEventCount));
    broadcast_line(line);

    uint32_t previous_t_us = 0U;
    for (size_t index = 0; index < kSpinEchoDemoEventCount; ++index) {
        const auto& event = kSpinEchoDemo[index];
        if (event.t_us > previous_t_us) {
            k_busy_wait(event.t_us - previous_t_us);
        }
        snprintk(
            line,
            sizeof(line),
            "seq_event index=%u t_us=%u channel=%s value=%d\n",
            static_cast<unsigned int>(index),
            static_cast<unsigned int>(event.t_us),
            event.channel,
            event.value);
        broadcast(line);
        previous_t_us = event.t_us;
    }

    ++g_sequence_runs;
    g_sequence_running = false;
    snprintk(line, sizeof(line), "seq_done name=spin_echo_demo total_us=%u runs=%u", 800U, static_cast<unsigned int>(g_sequence_runs));
    broadcast_line(line);
}

void trim_line(char* line) {
    size_t length = strlen(line);
    while (length > 0U && (line[length - 1U] == '\r' || line[length - 1U] == '\n' || line[length - 1U] == ' ')) {
        line[length - 1U] = '\0';
        --length;
    }
}

void handle_command(const char* port_name, char* line) {
    trim_line(line);
    if (line[0] == '\0') {
        return;
    }

    char response[kLineBufferSize];
    snprintk(response, sizeof(response), "cmd_port=%s cmd=%s", port_name, line);
    broadcast_line(response);

    if (strcmp(line, "HELP") == 0) {
        print_help();
    } else if (strcmp(line, "PING") == 0) {
        snprintk(response, sizeof(response), "PONG controller=stm32_sequence state=%s", g_sequence_running ? "running" : "idle");
        broadcast_line(response);
    } else if (strcmp(line, "STATUS") == 0) {
        print_status();
    } else if (strcmp(line, "RUN DEMO") == 0) {
        play_spin_echo_demo();
    } else {
        broadcast_line("error unknown_command");
        print_help();
    }
}

void append_received_byte(UartPort& port, unsigned char byte) {
    if (port.line_ready) {
        return;
    }

    if (byte == '\r' || byte == '\n') {
        if (port.command_length > 0U) {
            port.command[port.command_length] = '\0';
            port.line_ready = true;
        }
        return;
    }

    if (byte == '\b' || byte == 0x7f) {
        if (port.command_length > 0U) {
            --port.command_length;
            port.command[port.command_length] = '\0';
        }
        return;
    }

    if (port.command_length + 1U < kCommandBufferSize) {
        port.command[port.command_length] = static_cast<char>(byte);
        ++port.command_length;
        return;
    }

    port.command_length = 0U;
    port.command[0] = '\0';
    port.overflow = true;
}

void uart_irq_handler(const struct device* uart, void* user_data) {
    UartPort* port = static_cast<UartPort*>(user_data);
    if (port == nullptr) {
        return;
    }

    uart_irq_update(uart);
    while (uart_irq_rx_ready(uart)) {
        unsigned char bytes[16];
        const int read_count = uart_fifo_read(uart, bytes, sizeof(bytes));
        if (read_count <= 0) {
            break;
        }
        for (int index = 0; index < read_count; ++index) {
            append_received_byte(*port, bytes[index]);
        }
    }
}

void initialize_uart_interrupts() {
    for (size_t index = 0; index < sizeof(g_ports) / sizeof(g_ports[0]); ++index) {
        UartPort& port = g_ports[index];
        if (!device_is_ready(port.device)) {
            continue;
        }
        uart_irq_callback_user_data_set(port.device, uart_irq_handler, &port);
        uart_irq_rx_enable(port.device);
    }
}

void process_ready_commands() {
    for (size_t index = 0; index < sizeof(g_ports) / sizeof(g_ports[0]); ++index) {
        UartPort& port = g_ports[index];
        char command[kCommandBufferSize] = {};
        bool has_line = false;
        bool had_overflow = false;

        const unsigned int key = irq_lock();
        if (port.line_ready) {
            strncpy(command, port.command, sizeof(command) - 1U);
            port.line_ready = false;
            port.command_length = 0U;
            port.command[0] = '\0';
            has_line = true;
        }
        if (port.overflow) {
            port.overflow = false;
            had_overflow = true;
        }
        irq_unlock(key);

        if (had_overflow) {
            broadcast_line("error command_too_long");
        }
        if (has_line) {
            handle_command(port.name, command);
        }
    }
}

void poll_uart_commands() {
    int64_t last_heartbeat_ms = k_uptime_get();

    initialize_uart_interrupts();

    broadcast_line("mri_sequence_controller board=stm32f407vg mode=irq_uart");
    broadcast_line("uart_irq active=usart1,usart2,usart3,usart6 baud=57600");
    broadcast_line("gpio_outputs=disabled reason=external_camera_wifi_pins_unknown");
    print_help();

    while (true) {
        process_ready_commands();

        const int64_t now_ms = k_uptime_get();
        if (!g_sequence_running && now_ms - last_heartbeat_ms >= 5000) {
            char line[kLineBufferSize];
            snprintk(line, sizeof(line), "heartbeat state=idle uptime_ms=%lld", static_cast<long long>(now_ms));
            broadcast_line(line);
            last_heartbeat_ms = now_ms;
        }
        k_sleep(K_MSEC(1));
    }
}

}  // namespace

int main() {
    poll_uart_commands();
    return 0;
}
