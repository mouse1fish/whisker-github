/*
 * selftest.c —— 运行时自检（不经过编译器，手写 Actor）
 *
 * 验证点：
 *   1. 两 Actor 乒乓 100 万条消息，顺序与计数正确
 *   2. 多工作线程下消息不丢、不重
 *   3. 静止检测正确（whisker_sched_run 在全部处理完后返回）
 *   4. 批量扇出：1 个协调者向 64 个工人各发 1000 条
 */
#define WIN32_LEAN_AND_MEAN
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "whisker_runtime.h"

/* ---------- 乒乓 ---------- */
enum { PING = 1, PONG = 2 };

typedef struct { int32_t tag; int64_t v; int64_t final; } EnvBounce;

typedef struct {
    WhiskerActor base;
    WhiskerActor* peer;
    int64_t    limit;
    int64_t    count;
    int64_t    total;
    int64_t    last;
    int64_t    sum;
} Bouncer;

static void Bounce_init(Bouncer* self, WhiskerActor* peer, int64_t limit, int64_t total) {
    self->peer = peer;
    self->limit = limit;
    self->count = 0;
    self->total = total;
    self->last = 0;
    self->sum = 0;
}

static void Bounce_dispatch(WhiskerActor* a, void* payload) {
    Bouncer* self = (Bouncer*)a;
    EnvBounce* e = (EnvBounce*)payload;
    self->count++;
    self->last = e->v;
    self->sum += e->v;
    if (self->count < self->total) {
        EnvBounce* out = (EnvBounce*)whisker_msg_new(sizeof(EnvBounce));
        out->tag = (e->tag == PING) ? PONG : PING;
        out->v = e->v + 1;
        whisker_send(self->peer, out);
    }
    whisker_msg_free(e);
}

static Bouncer* Bouncer_new(WhiskerActor* peer, int64_t limit, int64_t total) {
    Bouncer* a = (Bouncer*)whisker_actor_new("Bouncer", sizeof(Bouncer), Bounce_dispatch);
    Bounce_init(a, peer, limit, total);
    return a;
}

/* ---------- 扇出 ---------- */
enum { WORK = 1, DONE = 2 };

typedef struct { int32_t tag; int64_t v; } EnvWork;

typedef struct {
    WhiskerActor base;
    WhiskerActor* boss;
    int64_t    got;
    int64_t    target;
} Worker;

static void Work_dispatch(WhiskerActor* a, void* payload) {
    Worker* self = (Worker*)a;
    EnvWork* e = (EnvWork*)payload;
    self->got++;
    if (self->got == self->target) {
        EnvWork* out = (EnvWork*)whisker_msg_new(sizeof(EnvWork));
        out->tag = DONE;
        out->v = e->v;
        whisker_send(self->boss, out);
    }
    whisker_msg_free(e);
}

static Worker* Worker_new(WhiskerActor* boss, int64_t target, int64_t seed) {
    Worker* a = (Worker*)whisker_actor_new("Worker", sizeof(Worker), Work_dispatch);
    a->boss = boss;
    a->target = target;
    a->got = 0;
    return a;
}

enum { BOSS_SPAWN = 1, BOSS_REPORT = 2 };

typedef struct { int32_t tag; int64_t n; } EnvBoss;

static WhiskerActor* g_workers[64];
static int g_nworkers_created = 0;
static int64_t g_reports = 0;
static int64_t g_expected = 0;

static void Boss_dispatch(WhiskerActor* a, void* payload) {
    EnvBoss* e = (EnvBoss*)payload;
    if (e->tag == BOSS_SPAWN) {
        for (int64_t i = 0; i < e->n; i++) {
            Worker* w = Worker_new(a, 1000, i);
            g_workers[g_nworkers_created++] = (WhiskerActor*)w;
        }
        /* 每个工人 1000 条，全部由主 Actor 扇出 */
        for (int i = 0; i < g_nworkers_created; i++) {
            for (int64_t k = 0; k < 1000; k++) {
                EnvWork* m = (EnvWork*)whisker_msg_new(sizeof(EnvWork));
                m->tag = WORK;
                m->v = (int64_t)i * 1000 + k;
                whisker_send(g_workers[i], m);
            }
        }
    } else if (e->tag == BOSS_REPORT) {
        g_reports++;
    }
    whisker_msg_free(e);
}

static WhiskerActor* Boss_new(void) {
    return whisker_actor_new("Boss", sizeof(WhiskerActor), Boss_dispatch);
}

int main(void) {
    whisker_runtime_init(0);
    printf("=== Whisker 运行时自检（%d 工作线程）===\n", whisker_cores());

    /* 1) 乒乓：两 Actor 各领 100 万条上限，共 1999999 跳
     *    期望：x 收到奇数 v(1..1999999) 共 1e6 条，y 收到偶数 v(2..1999998) 共 999999 条
     *    额外做一次求和校验（能同时揪出丢消息与重复消息） */
    double t0 = whisker_now_ms();
    Bouncer* x = Bouncer_new(NULL, 0, 1000000);
    Bouncer* y = Bouncer_new((WhiskerActor*)x, 0, 1000000);
    x->peer = (WhiskerActor*)y;
    EnvBounce* kick = (EnvBounce*)whisker_msg_new(sizeof(EnvBounce));
    kick->tag = PING; kick->v = 1;
    whisker_send((WhiskerActor*)x, kick);
    whisker_sched_run();
    double t1 = whisker_now_ms();

    int64_t total_msgs = x->count + y->count;
    int64_t expect_sum = 1999999LL * 2000000LL / 2;   /* 1+2+...+1999999 */
    int ok_bounce = (x->count == 1000000) && (x->last == 1999999) &&
                    (y->count == 999999) && (y->last == 1999998) &&
                    (x->sum + y->sum == expect_sum);
    printf("[1] 乒乓: x=%lld(last %lld) y=%lld(last %lld) 求和校验=%s → %s\n",
           (long long)x->count, (long long)x->last, (long long)y->count, (long long)y->last,
           (x->sum + y->sum == expect_sum) ? "对" : "错", ok_bounce ? "OK" : "FAIL");
    printf("    共 %lld 条消息，用时 %.1f ms → %.1f 万条/秒\n",
           (long long)total_msgs, t1 - t0, (double)total_msgs / (t1 - t0) / 10.0);

    /* 2) 扇出到 64 个工人 */
    t0 = whisker_now_ms();
    g_expected = 64;
    WhiskerActor* boss = Boss_new();
    EnvBoss* sp = (EnvBoss*)whisker_msg_new(sizeof(EnvBoss));
    sp->tag = BOSS_SPAWN; sp->n = 64;
    whisker_send(boss, sp);
    whisker_sched_run();
    t1 = whisker_now_ms();

    int64_t total_got = 0;
    for (int i = 0; i < g_nworkers_created; i++) total_got += ((Worker*)g_workers[i])->got;
    int ok_fan = (g_nworkers_created == 64) && (total_got == 64000) && (g_reports == 64);
    printf("[2] 扇出: 工人=%d 收消息=%lld/64000 回报=%lld/64 → %s  用时 %.1f ms\n",
           g_nworkers_created, (long long)total_got, (long long)g_reports,
           ok_fan ? "OK" : "FAIL", t1 - t0);

    whisker_stats();
    whisker_runtime_shutdown();
    printf("=== %s ===\n", (ok_bounce && ok_fan) ? "全部通过" : "存在失败项");
    return (ok_bounce && ok_fan) ? 0 : 1;
}