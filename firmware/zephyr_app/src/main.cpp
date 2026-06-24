#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iterator>

namespace {

struct SequenceEvent {
    std::uint32_t t_us;
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

constexpr std::size_t kCommandBufferSize = 96U;

bool g_sequence_running = false;
std::uint32_t g_sequence_runs = 0U;

void print_help() {
    printk("commands:\n");
    printk("  HELP      - show command list\n");
    printk("  PING      - check serial link\n");
    printk("  STATUS    - print controller state\n");
    printk("  RUN DEMO  - play built-in spin echo demo\n");
}

void print_status() {
    printk(
        "status state=%s sequence=spin_echo_demo events=%u runs=%u uptime_ms=%lld\n",
        g_sequence_running ? "running" : "idle",
        static_cast<unsigned int>(std::size(kSpinEchoDemo)),
        static_cast<unsigned int>(g_sequence_runs),
        static_cast<long long>(k_uptime_get()));
}

void play_spin_echo_demo() {
    if (g_sequence_running) {
        printk("error sequence_already_running\n");
        return;
    }

    g_sequence_running = true;
    printk("seq_start name=spin_echo_demo events=%u\n", static_cast<unsigned int>(std::size(kSpinEchoDemo)));

    std::uint32_t previous_t_us = 0U;
    for (std::size_t index = 0; index < std::size(kSpinEchoDemo); ++index) {
        const auto& event = kSpinEchoDemo[index];
        if (event.t_us > previous_t_us) {
            k_busy_wait(event.t_us - previous_t_us);
        }
        printk(
            "seq_event index=%u t_us=%u channel=%s value=%d\n",
            static_cast<unsigned int>(index),
            static_cast<unsigned int>(event.t_us),
            event.channel,
            event.value);
        previous_t_us = event.t_us;
    }

    ++g_sequence_runs;
    g_sequence_running = false;
    printk("seq_done name=spin_echo_demo total_us=%u runs=%u\n", 800U, static_cast<unsigned int>(g_sequence_runs));
}

void trim_line(char* line) {
    std::size_t length = std::strlen(line);
    while (length > 0U && (line[length - 1U] == '\r' || line[length - 1U] == '\n' || line[length - 1U] == ' ')) {
        line[length - 1U] = '\0';
        --length;
    }
}

void handle_command(char* line) {
    trim_line(line);
    if (line[0] == '\0') {
        return;
    }

    printk("cmd=%s\n", line);
    if (std::strcmp(line, "HELP") == 0) {
        print_help();
    } else if (std::strcmp(line, "PING") == 0) {
        printk("PONG controller=stm32_sequence state=%s\n", g_sequence_running ? "running" : "idle");
    } else if (std::strcmp(line, "STATUS") == 0) {
        print_status();
    } else if (std::strcmp(line, "RUN DEMO") == 0) {
        play_spin_echo_demo();
    } else {
        printk("error unknown_command\n");
        print_help();
    }
}

void poll_uart_commands(const device* uart) {
    char command[kCommandBufferSize] = {};
    std::size_t command_length = 0U;
    std::int64_t last_heartbeat_ms = k_uptime_get();

    print_help();
    while (true) {
        unsigned char byte = 0U;
        if (uart_poll_in(uart, &byte) == 0) {
            if (byte == '\r' || byte == '\n') {
                command[command_length] = '\0';
                handle_command(command);
                command_length = 0U;
                command[0] = '\0';
            } else if (byte == '\b' || byte == 0x7f) {
                if (command_length > 0U) {
                    --command_length;
                    command[command_length] = '\0';
                }
            } else if (command_length + 1U < kCommandBufferSize) {
                command[command_length] = static_cast<char>(byte);
                ++command_length;
            } else {
                command_length = 0U;
                command[0] = '\0';
                printk("error command_too_long\n");
            }
        }

        const std::int64_t now_ms = k_uptime_get();
        if (!g_sequence_running && now_ms - last_heartbeat_ms >= 5000) {
            printk("heartbeat state=idle uptime_ms=%lld\n", static_cast<long long>(now_ms));
            last_heartbeat_ms = now_ms;
        }
        k_sleep(K_MSEC(5));
    }
}

}  // namespace

int main() {
    const device* uart = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

    printk("mri_sequence_controller board=stm32f407vg mode=uart_only\n");
    printk("gpio_outputs=disabled reason=external_camera_wifi_pins_unknown\n");

    if (!device_is_ready(uart)) {
        printk("error console_uart_not_ready\n");
        return 1;
    }

    poll_uart_commands(uart);
    return 0;
}
