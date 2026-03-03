#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

void win() {
    char buf[64];
    int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) {
        write(1, "flag.txt not found\n", 19);
        exit(1);
    }
    int n = read(fd, buf, sizeof(buf) - 1);
    if (n > 0) buf[n] = '\0';
    close(fd);
    write(1, "You got it! Flag: ", 18);
    write(1, buf, n > 0 ? n : 0);
    write(1, "\n", 1);
    exit(0);
}

void vuln() {
    char buf[64];
    write(1, "Enter your name: ", 17);
    read(0, buf, 256);
    write(1, "Hello, ", 7);
    write(1, buf, strlen(buf));
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    write(1, "=== GreetBot v1.0 ===\n", 22);
    write(1, "A simple greeter service.\n", 26);
    vuln();
    write(1, "\nGoodbye!\n", 10);
    return 0;
}
