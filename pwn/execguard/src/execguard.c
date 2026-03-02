/*
 * execguard.c — CTF challenge source (ORGANIZER ONLY)
 *
 * Seccomp-hardened binary.  The developer blocked execve and execveat
 * to prevent shell spawning, but forgot that read/write/open are still
 * perfectly capable of leaking the flag without ever exec'ing anything.
 *
 * Intended exploit path:
 *   1. Find stack overflow in vuln()  (read 512 → 64-byte buf)
 *   2. NX disabled → shellcode on stack
 *   3. Return to jmp_rsp gadget (fixed address, no PIE) → jmp rsp → shellcode
 *   4. Shellcode writes "flag.txt\0" to bss_shellstr (fixed BSS address)
 *   5. open("flag.txt", O_RDONLY)  — syscall 2, NOT blocked
 *   6. read(fd, buf, 64)           — syscall 0, NOT blocked
 *   7. write(1, buf, n)            — syscall 1, NOT blocked → flag printed!
 *
 * Key insight: blocking exec* doesn't make a binary safe if read/write/open
 * are still permitted and the attacker can run arbitrary shellcode.
 *
 * Compile:
 *   gcc -fno-stack-protector -no-pie -z execstack -o execguard execguard.c
 *
 * Key addresses after compile:
 *   bss_shellstr   : `nm execguard | grep bss_shellstr`
 *   jmp_rsp_gadget : `objdump -d execguard | grep jmp_rsp`
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <stddef.h>

/* Named BSS symbol at a fixed address (no PIE).
 * Players use it to store "flag.txt\0" for the open() call.
 * 64 bytes total: [0..7] path, [8..63] read buffer.          */
char bss_shellstr[64];

/*
 * Trampoline gadget — intentionally exposed.
 * Jumping here executes `jmp rsp`, transferring control to whatever
 * is on top of the stack (the shellcode placed there by the overflow).
 * Find it via `objdump -d execguard | grep jmp_rsp`.
 */
__attribute__((naked, noinline))
void jmp_rsp_gadget(void) {
    __asm__("jmp *%rsp\n\t"
            "ret\n\t");
}

void setup_seccomp(void) {
    struct sock_filter filter[] = {
        /* load syscall number */
        BPF_STMT(BPF_LD  | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),

        /* block execve (59) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execve,   0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

        /* block execveat (322) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execveat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

        /* allow everything else — open/read/write still work! */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len    = (unsigned short)(sizeof filter / sizeof filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog);
}

void vuln(void) {
    char buf[64];
    write(1, "Input: ", 7);
    read(0, buf, 512);          /* BUG: 512 bytes → 64-byte buf */
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    write(1, "=== ExecGuard v1 ===\n", 21);
    write(1, "execve: BLOCKED. Nice try.\n", 27);
    setup_seccomp();
    vuln();
    return 0;
}
