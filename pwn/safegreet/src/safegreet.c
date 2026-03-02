/*
 * safegreet.c — CTF challenge source (ORGANIZER ONLY — do not distribute)
 *
 * Fork-based TCP greeting server with stack canary.
 * The canary stays the same across all connections (fork, not exec).
 * Intended exploit: brute-force canary byte-by-byte, then ret2win.
 *
 * Compile:
 *   gcc -fstack-protector-all -no-pie -o safegreet safegreet.c
 *
 * Key vulnerability: read(0, buf, BUFSIZE * 2) reads 128 bytes into 64-byte buf.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT    4445
#define BUFSIZE 64

/* ---------- hidden win function ---------- */
void win() {
    char fbuf[64];
    int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) { write(1, "flag.txt not found\n", 19); exit(1); }
    int n = read(fd, fbuf, (int)sizeof(fbuf) - 1);
    close(fd);
    if (n > 0) fbuf[n] = '\0';
    write(1, "Canary cracked! Flag: ", 22);
    write(1, fbuf, n > 0 ? (size_t)n : 0);
    write(1, "\n", 1);
    exit(0);
}

/* ---------- vulnerable function ---------- */
void vuln() {
    char buf[BUFSIZE];                  /* 64-byte buffer on the stack    */
    write(1, "Name: ", 6);
    read(0, buf, BUFSIZE * 2);          /* BUG: reads 128 into 64-byte buf */
    write(1, "Hello!\n", 7);
}

/* ---------- per-connection handler ---------- */
void handle_client(int sock) {
    dup2(sock, 0);   /* redirect stdin  → socket */
    dup2(sock, 1);   /* redirect stdout → socket */
    close(sock);

    write(1, "=== SafeGreet v2 ===\n", 21);
    write(1, "Stack canary protection: ENABLED\n", 33);
    vuln();
    write(1, "Goodbye!\n", 9);
    exit(0);
}

/* ---------- fork-based TCP server ---------- */
int main() {
    signal(SIGCHLD, SIG_IGN);   /* auto-reap children */

    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) { perror("socket"); return 1; }

    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(srv, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }
    listen(srv, 32);

    while (1) {
        int client = accept(srv, NULL, NULL);
        if (client < 0) continue;

        pid_t pid = fork();      /* fork — child inherits parent's canary */
        if (pid < 0) { close(client); continue; }
        if (pid == 0) {          /* child */
            close(srv);
            handle_client(client);
        }
        close(client);           /* parent */
    }
    return 0;
}
