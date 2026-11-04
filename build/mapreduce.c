/* 由 whiskerc 生成的 C 代码（源文件：mapreduce.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Worker {
    WhiskerActor base;
} A_Worker;

typedef struct A_Main {
    WhiskerActor base;
    int64_t v_n;
    int64_t v_got;
    int64_t v_total;
    int64_t v_span;
} A_Main;

typedef struct M_Worker_Slice { int64_t v_lo; int64_t v_hi; WhiskerActor* v_reply; } M_Worker_Slice;
enum { T_Worker_Slice = 1 };
typedef struct E_Worker { int32_t tag; union { M_Worker_Slice h_Slice; } u; } E_Worker;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Part { int64_t v_s; } M_Main_Part;
enum { T_Main_Start = 1, T_Main_Part = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Part h_Part; } u; } E_Main;

static void D_Worker(WhiskerActor* a, void* payload);
static A_Worker* N_Worker(void);
static void H_Worker_Slice(A_Worker* self, int64_t v_lo, int64_t v_hi, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Part(A_Main* self, int64_t v_s);

static void H_Worker_Slice(A_Worker* self, int64_t v_lo, int64_t v_hi, WhiskerActor* v_reply) {
    int64_t v_s = INT64_C(0);
    int64_t v_i = v_lo;
    while ((v_i <= v_hi)) {
        v_s = (v_s + ((v_i % INT64_C(97)) * (v_i % INT64_C(97))));
        v_i = (v_i + INT64_C(1));
    }
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Part;
        _e1->u.h_Part.v_s = v_s;
        whisker_send((WhiskerActor*)(v_reply), _e1);
    }
}

static void H_Main_Start(A_Main* self) {
    int64_t v_k = INT64_C(0);
    while ((v_k < self->v_n)) {
        WhiskerActor* v_w = ((WhiskerActor*)N_Worker());
        int64_t v_lo = ((v_k * (self->v_span / self->v_n)) + INT64_C(1));
        int64_t v_hi = ((v_k + INT64_C(1)) * (self->v_span / self->v_n));
        {
            E_Worker* _e2 = (E_Worker*)whisker_msg_new(sizeof(E_Worker));
            _e2->tag = T_Worker_Slice;
            _e2->u.h_Slice.v_lo = v_lo;
            _e2->u.h_Slice.v_hi = v_hi;
            _e2->u.h_Slice.v_reply = ((WhiskerActor*)self);
            whisker_send((WhiskerActor*)(v_w), _e2);
        }
        v_k = (v_k + INT64_C(1));
    }
}

static void H_Main_Part(A_Main* self, int64_t v_s) {
    self->v_got = (self->v_got + INT64_C(1));
    self->v_total = (self->v_total + v_s);
    if ((self->v_got == self->v_n)) {
        whisker_print_begin();
        whisker_print_int(self->v_n);
        whisker_print_str(" 个分片汇总结果 = ");
        whisker_print_int(self->v_total);
        whisker_print_end();
    }
}

static void D_Worker(WhiskerActor* a, void* payload) {
    A_Worker* self = (A_Worker*)a;
    E_Worker* e = (E_Worker*)payload;
    switch (e->tag) {
    case T_Worker_Slice: H_Worker_Slice(self, e->u.h_Slice.v_lo, e->u.h_Slice.v_hi, e->u.h_Slice.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Part: H_Main_Part(self, e->u.h_Part.v_s); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Worker* N_Worker(void) {
    A_Worker* a = (A_Worker*)whisker_actor_new("Worker", sizeof(A_Worker), D_Worker);
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_n = INT64_C(32);
    a->v_got = INT64_C(0);
    a->v_total = INT64_C(0);
    a->v_span = INT64_C(2000000);
    return a;
}

int main(void) {
    whisker_runtime_init(0);
    {
        A_Main* root = N_Main();
        E_Main* m = (E_Main*)whisker_msg_new(sizeof(E_Main));
        m->tag = T_Main_Start;
        whisker_send((WhiskerActor*)root, m);
    }
    whisker_sched_run();
    whisker_runtime_shutdown();
    return 0;
}
