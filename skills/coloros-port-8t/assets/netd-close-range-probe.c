#define _GNU_SOURCE
#include <fcntl.h>
#include <spawn.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
extern char **environ;
int main(void) {
    int fd = open("/dev/null", O_RDONLY);
    if (fd < 3) return 2;
    char command[256];
    snprintf(command, sizeof(command), "test ! -e /proc/self/fd/%d && test -e /proc/self/fd/200", fd);
    char *args[] = {"/system/bin/sh", "-c", command, NULL};
    posix_spawnattr_t attr;
    if (posix_spawnattr_init(&attr)) return 3;
    if (posix_spawnattr_setflags(&attr, 0x100)) return 4;
    pid_t pid;
    posix_spawn_file_actions_t actions;
    if (posix_spawn_file_actions_init(&actions)) return 7;
    if (posix_spawn_file_actions_adddup2(&actions, fd, 200)) return 8;
    int err = posix_spawn(&pid, args[0], &actions, &attr, args, environ);
    if (err) { printf("spawn error=%d\n", err); return 5; }
    int status;
    if (waitpid(pid, &status, 0) != pid) return 6;
    int parent_flags = fcntl(fd, F_GETFD);
    printf("child_status=%d parent_fd_flags=%d\n", status, parent_flags);
    return !(WIFEXITED(status) && WEXITSTATUS(status) == 0 && parent_flags == 0);
}
