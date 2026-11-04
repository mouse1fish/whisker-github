/*
 * whisker_runtime.c —— Whisker Actor 运行时（M0 实现）
 *
 * 同时只持有一把全局调度锁，保证：
 *   - 消息入队与 Actor 状态迁移的原子性（不会丢唤醒）
 *   - 消息处理全程在锁外执行 → 多 Actor 真正并行
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "whisker_runtime.h"

#define WHISKER_MAX_WORKERS 256
#define WHISKER_PRINTBUF    4096

/* ---------------- 全局状态 ---------------- */
static SRWLOCK           g_lock     = SRWLOCK_INIT;
static CONDITION_VARIABLE g_work_cv = CONDITION_VARIABLE_INIT;
static CONDITION_VARIABLE g_idle_cv = CONDITION_VARIABLE_INIT;

static WhiskerActor* g_qhead = NULL;
static WhiskerActor* g_qtail = NULL;
static int        g_queued = 0;
static int        g_running = 0;
static int        g_shutdown = 0;
static int        g_inited = 0;
static int        g_nworkers = 0;
static int        g_idle_workers = 0;   /* 正阻塞在 g_work_cv 上的工作线程数 */
static HANDLE     g_threads[WHISKER_MAX_WORKERS];

/* 邮箱节点对象池：稳态下不再走 malloc/free */
#define WHISKER_POOL_MAX 16384
static WhiskerMsgNode* g_node_pool = NULL;
static int          g_pool_count = 0;

/* Actor 注册表：仅用于退出时统一释放 */
static WhiskerActor** g_all = NULL;
static size_t      g_all_count = 0;
static size_t      g_all_cap = 0;

/* 计数在 g_lock 保护下自增（避免跨核原子操作造成的缓存行争用） */
static int64_t g_msgs_sent = 0;
static int64_t g_msgs_handled = 0;

static LARGE_INTEGER g_freq;
static LARGE_INTEGER g_t0;

/* per-thread 打印缓冲，保证单条 print 输出不被其它 Actor 打断 */
static __declspec(thread) char t_pbuf[WHISKER_PRINTBUF];
static __declspec(thread) int  t_plen = 0;
static SRWLOCK g_print_lock = SRWLOCK_INIT;

/* ---------------- 就绪队列（调用方必须持锁） ---------------- */
static void q_push(WhiskerActor* a) {
    a->qnext = NULL;
    if (g_qtail) g_qtail->qnext = a; else g_qhead = a;
    g_qtail = a;
    g_queued++;
}

static WhiskerActor* q_pop(void) {
    WhiskerActor* a = g_qhead;
    if (!a) return NULL;
    g_qhead = a->qnext;
    if (!g_qhead) g_qtail = NULL;
    a->qnext = NULL;
    g_queued--;
    return a;
}

/* 只唤醒一个空闲工作线程（调用方持锁）。
 * 不预扣 g_idle_workers，宁可偶发多唤醒，绝不丢唤醒。 */
static void wake_one_worker(void) {
    if (g_idle_workers > 0) WakeConditionVariable(&g_work_cv);
}

/* 邮箱节点分配/回收（调用方持锁） */
static WhiskerMsgNode* node_alloc(void) {
    if (g_node_pool) {
        WhiskerMsgNode* n = g_node_pool;
        g_node_pool = n->next;
        g_pool_count--;
        return n;
    }
    WhiskerMsgNode* n = (WhiskerMsgNode*)malloc(sizeof(WhiskerMsgNode));
    if (!n) { fprintf(stderr, "[whisker] 邮箱节点分配失败\n"); exit(1); }
    return n;
}

static int node_release_chain(WhiskerMsgNode* chain, int len, WhiskerMsgNode* tail) {
    /* 调用方持锁；池满时返回 0，由调用方在锁外释放 */
    if (g_pool_count + len <= WHISKER_POOL_MAX) {
        tail->next = g_node_pool;
        g_node_pool = chain;
        g_pool_count += len;
        return 1;
    }
    return 0;
}

/* ---------------- 工作线程 ---------------- */
static DWORD WINAPI whisker_worker(LPVOID param) {
    (void)param;
    for (;;) {
        AcquireSRWLockExclusive(&g_lock);
        while (g_qhead == NULL && !g_shutdown) {
            g_idle_workers++;
            SleepConditionVariableSRW(&g_work_cv, &g_lock, INFINITE, 0);
            g_idle_workers--;
        }
        if (g_qhead == NULL && g_shutdown) {
            ReleaseSRWLockExclusive(&g_lock);
            break;
        }
        WhiskerActor* a = q_pop();
        a->state = WHISKER_RUNNING;
        g_running++;
        WhiskerMsgNode* batch = a->head;   /* 整批取走，锁外处理 */
        a->head = NULL;
        a->tail = NULL;
        ReleaseSRWLockExclusive(&g_lock);

        int len = 0;
        WhiskerMsgNode* tail = NULL;
        WhiskerMsgNode* n = batch;
        while (n) {
            WhiskerMsgNode* nx = n->next;
            tail = n;
            len++;
            a->dispatch(a, n->payload);
            n = nx;
        }

        AcquireSRWLockExclusive(&g_lock);
        g_msgs_handled += len;
        g_running--;
        int pooled = node_release_chain(batch, len, tail);
        if (a->head != NULL) {
            /* 处理期间又有新消息到达 → 重新入队 */
            a->state = WHISKER_QUEUED;
            q_push(a);
            wake_one_worker();
        } else {
            a->state = WHISKER_IDLE;
            if (g_queued == 0 && g_running == 0) {
                WakeAllConditionVariable(&g_idle_cv);   /* 系统静止 */
            }
        }
        ReleaseSRWLockExclusive(&g_lock);

        if (!pooled) {              /* 对象池已满，锁外释放节点 */
            n = batch;
            while (n) { WhiskerMsgNode* nx = n->next; free(n); n = nx; }
        }
    }
    return 0;
}

/* ---------------- 公共 API ---------------- */
int whisker_cores(void) {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return (int)si.dwNumberOfProcessors;
}

void whisker_runtime_init(int workers) {
    if (g_inited) return;
    QueryPerformanceFrequency(&g_freq);
    QueryPerformanceCounter(&g_t0);

    if (workers <= 0) {
        const char* env = getenv("WHISKER_WORKERS");
        workers = (env && *env) ? atoi(env) : whisker_cores();
    }
    if (workers < 1) workers = 1;
    if (workers > WHISKER_MAX_WORKERS) workers = WHISKER_MAX_WORKERS;
    g_nworkers = workers;

    for (int i = 0; i < workers; i++) {
        g_threads[i] = CreateThread(NULL, 0, whisker_worker, NULL, 0, NULL);
        if (!g_threads[i]) {
            fprintf(stderr, "[whisker] 工作线程创建失败（已创建 %d 个）\n", i);
            g_nworkers = i;
            break;
        }
    }
    g_inited = 1;
}

WhiskerActor* whisker_actor_new(const char* name, size_t size, WhiskerDispatchFn fn) {
    WhiskerActor* a = (WhiskerActor*)calloc(1, size);
    if (!a) { fprintf(stderr, "[whisker] Actor 分配失败\n"); exit(1); }
    a->name = name;
    a->dispatch = fn;
    a->state = WHISKER_IDLE;

    AcquireSRWLockExclusive(&g_lock);
    if (g_all_count == g_all_cap) {
        size_t cap = g_all_cap ? g_all_cap * 2 : 64;
        WhiskerActor** ns = (WhiskerActor**)realloc(g_all, cap * sizeof(WhiskerActor*));
        if (ns) { g_all = ns; g_all_cap = cap; }
    }
    if (g_all_count < g_all_cap) g_all[g_all_count++] = a;
    ReleaseSRWLockExclusive(&g_lock);
    return a;
}

void* whisker_msg_new(size_t size) {
    void* p = calloc(1, size);
    if (!p) { fprintf(stderr, "[whisker] 消息分配失败\n"); exit(1); }
    return p;
}

void whisker_msg_free(void* p) {
    free(p);
}

void whisker_send(WhiskerActor* target, void* payload) {
    if (!target) {
        fprintf(stderr, "[whisker] 向空 Actor 引用发送消息（消息已丢弃）\n");
        whisker_msg_free(payload);
        return;
    }
    AcquireSRWLockExclusive(&g_lock);
    WhiskerMsgNode* n = node_alloc();
    n->payload = payload;
    n->next = NULL;

    if (target->tail) target->tail->next = n; else target->head = n;
    target->tail = n;
    g_msgs_sent++;

    if (target->state == WHISKER_IDLE) {
        target->state = WHISKER_QUEUED;
        q_push(target);
        wake_one_worker();
    }
    ReleaseSRWLockExclusive(&g_lock);
}

void whisker_sched_run(void) {
    AcquireSRWLockExclusive(&g_lock);
    while (!(g_queued == 0 && g_running == 0)) {
        SleepConditionVariableSRW(&g_idle_cv, &g_lock, INFINITE, 0);
    }
    ReleaseSRWLockExclusive(&g_lock);
}

void whisker_runtime_shutdown(void) {
    if (!g_inited) return;
    AcquireSRWLockExclusive(&g_lock);
    g_shutdown = 1;
    WakeAllConditionVariable(&g_work_cv);
    ReleaseSRWLockExclusive(&g_lock);

    for (int i = 0; i < g_nworkers; i++) {
        if (g_threads[i]) {
            WaitForSingleObject(g_threads[i], INFINITE);
            CloseHandle(g_threads[i]);
            g_threads[i] = NULL;
        }
    }

    const char* st = getenv("WHISKER_STATS");
    if (st && *st && *st != '0') whisker_stats();   /* 先出统计，再释放 */

    for (size_t i = 0; i < g_all_count; i++) {
        WhiskerActor* a = g_all[i];
        WhiskerMsgNode* n = a->head;
        while (n) { WhiskerMsgNode* nx = n->next; whisker_msg_free(n->payload); free(n); n = nx; }
        free(a);
    }
    free(g_all);
    g_all = NULL; g_all_count = 0; g_all_cap = 0;

    while (g_node_pool) {           /* 回收邮箱节点对象池 */
        WhiskerMsgNode* n = g_node_pool;
        g_node_pool = n->next;
        free(n);
    }
    g_pool_count = 0;
    g_inited = 0;
}

double whisker_now_ms(void) {
    LARGE_INTEGER now;
    QueryPerformanceCounter(&now);
    return (double)(now.QuadPart - g_t0.QuadPart) * 1000.0 / (double)g_freq.QuadPart;
}

void whisker_stats(void) {
    printf("[whisker] 工作线程 %d | Actor %zu | 发送 %lld 条 | 处理 %lld 条 | 耗时 %.1f ms\n",
           g_nworkers, g_all_count,
           (long long)g_msgs_sent, (long long)g_msgs_handled, whisker_now_ms());
}

/* ---------------- 打印 ---------------- */
void whisker_print_begin(void) { t_plen = 0; t_pbuf[0] = '\0'; }

static void pbuf_append(const char* s) {
    if (!s) s = "(null)";
    int room = WHISKER_PRINTBUF - 1 - t_plen;
    if (room <= 0) return;
    int n = (int)strlen(s);
    if (n > room) n = room;
    memcpy(t_pbuf + t_plen, s, (size_t)n);
    t_plen += n;
    t_pbuf[t_plen] = '\0';
}

void whisker_print_int(int64_t v) {
    char tmp[32];
    _snprintf_s(tmp, sizeof(tmp), _TRUNCATE, "%lld", (long long)v);
    pbuf_append(tmp);
}

void whisker_print_bool(bool v) {
    pbuf_append(v ? "true" : "false");
}

void whisker_print_str(const char* s) {
    pbuf_append(s);
}

void whisker_print_end(void) {
    AcquireSRWLockExclusive(&g_print_lock);
    fputs(t_pbuf, stdout);
    fputc('\n', stdout);
    fflush(stdout);
    ReleaseSRWLockExclusive(&g_print_lock);
}
