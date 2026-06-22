#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

int main() {
    printk("MRI sequence controller scaffold\n");

    while (true) {
        k_sleep(K_SECONDS(1));
        printk("sequence controller heartbeat\n");
    }

    return 0;
}

