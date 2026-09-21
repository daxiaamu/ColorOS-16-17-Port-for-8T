#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
/* Loaded only by netd through an explicit dependency; no global preload. */
__attribute__((visibility("default")))
int close_range(unsigned first, unsigned last, int flags) {
    int saved_errno = errno;
    int ret = syscall(436, first, last, flags);
    if (ret == 0 || errno != ENOSYS || first != 3 || last != UINT_MAX || flags != 4)
        return ret;
    /* AOSP's former spawn fallback: child-only, no allocation, preserve flags. */
    struct rlimit limit;
    if (getrlimit(RLIMIT_NOFILE, &limit) != 0) return -1;
    if (limit.rlim_max > INT_MAX) { errno = EOVERFLOW; return -1; }
    for (int fd = 3; (rlim_t)fd < limit.rlim_max; ++fd) {
        int value;
        do { value = fcntl(fd, F_GETFD); } while (value == -1 && errno == EINTR);
        if (value == -1) {
            if (errno == EBADF) continue;
            return -1;
        }
        int result;
        do { result = fcntl(fd, F_SETFD, value | FD_CLOEXEC); }
        while (result == -1 && errno == EINTR);
        if (result == -1) return -1;
    }
    errno = saved_errno;
    return 0;
}
