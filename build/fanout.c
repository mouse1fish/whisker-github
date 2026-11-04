/* 由 whiskerc 生成的 C 代码（源文件：fanout.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Worker {
    WhiskerActor base;
} A_Worker;

typedef struct A_Main {
    WhiskerActor base;
    int64_t v_got;
    int64_t v_total;
    int64_t v_t0;
    int64_t v_serial;
    int64_t v_nworkers;
    int64_t v_span;
} A_Main;

typedef struct M_Worker_Chunk { int64_t v_lo; int64_t v_hi; WhiskerActor* v_reply; } M_Worker_Chunk;
enum { T_Worker_Chunk = 1 };
typedef struct E_Worker { int32_t tag; union { M_Worker_Chunk h_Chunk; } u; } E_Worker;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Result { int64_t v_part; } M_Main_Result;
enum { T_Main_Start = 1, T_Main_Result = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Result h_Result; } u; } E_Main;

static void D_Worker(WhiskerActor* a, void* payload);
static A_Worker* N_Worker(void);
static void H_Worker_Chunk(A_Worker* self, int64_t v_lo, int64_t v_hi, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Result(A_Main* self, int64_t v_part);

static void H_Worker_Chunk(A_Worker* self, int64_t v_lo, int64_t v_hi, WhiskerActor* v_reply) {
    int64_t v_s = INT64_C(0);
    int64_t v_i = v_lo;
    while ((v_i <= v_hi)) {
        v_s = (v_s + ((v_i % INT64_C(1000)) * (v_i % INT64_C(1000))));
        v_i = (v_i + INT64_C(1));
    }
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Result;
        _e1->u.h_Result.v_part = v_s;
        whisker_send((WhiskerActor*)(v_reply), _e1);
    }
}

static void H_Main_Start(A_Main* self) {
    whisker_print_begin();
    whisker_print_str("题目：对 1..");
    whisker_print_int(self->v_span);
    whisker_print_str(" 每个数取平方后累加");
    whisker_print_end();
    whisker_print_begin();
    whisker_print_str("");
    whisker_print_end();
    int64_t v_ts = ((int64_t)whisker_now_ms());
    int64_t v_s = INT64_C(0);
    int64_t v_i = INT64_C(1);
    while ((v_i <= self->v_span)) {
        v_s = (v_s + ((v_i % INT64_C(1000)) * (v_i % INT64_C(1000))));
        v_i = (v_i + INT64_C(1));
    }
    int64_t v_serial_ms = (((int64_t)whisker_now_ms()) - v_ts);
    self->v_serial = v_s;
    whisker_print_begin();
    whisker_print_str("串行（1 个 actor）  用时 ");
    whisker_print_int(v_serial_ms);
    whisker_print_str(" ms   结果 = ");
    whisker_print_int(v_s);
    whisker_print_end();
    self->v_t0 = ((int64_t)whisker_now_ms());
    int64_t v_k = INT64_C(0);
    while ((v_k < self->v_nworkers)) {
        WhiskerActor* v_w = ((WhiskerActor*)N_Worker());
        int64_t v_lo = ((v_k * (self->v_span / self->v_nworkers)) + INT64_C(1));
        int64_t v_hi = ((v_k + INT64_C(1)) * (self->v_span / self->v_nworkers));
        {
            E_Worker* _e2 = (E_Worker*)whisker_msg_new(sizeof(E_Worker));
            _e2->tag = T_Worker_Chunk;
            _e2->u.h_Chunk.v_lo = v_lo;
            _e2->u.h_Chunk.v_hi = v_hi;
            _e2->u.h_Chunk.v_reply = ((WhiskerActor*)self);
            whisker_send((WhiskerActor*)(v_w), _e2);
        }
        v_k = (v_k + INT64_C(1));
    }
}

static void H_Main_Result(A_Main* self, int64_t v_part) {
    self->v_got = (self->v_got + INT64_C(1));
    self->v_total = (self->v_total + v_part);
    if ((self->v_got == self->v_nworkers)) {
        whisker_print_begin();
        whisker_print_str("并行（");
        whisker_print_int(self->v_nworkers);
        whisker_print_str(" 个 actor）  用时 ");
        whisker_print_int((((int64_t)whisker_now_ms()) - self->v_t0));
        whisker_print_str(" ms   结果 = ");
        whisker_print_int(self->v_total);
        whisker_print_end();
        if ((self->v_total == self->v_serial)) {
            whisker_print_begin();
            whisker_print_str("结果校验：与串行完全一致");
            whisker_print_end();
        } else {
            whisker_print_begin();
            whisker_print_str("结果校验：不一致，请检查");
            whisker_print_end();
        }
    }
}

static void D_Worker(WhiskerActor* a, void* payload) {
    A_Worker* self = (A_Worker*)a;
    E_Worker* e = (E_Worker*)payload;
    switch (e->tag) {
    case T_Worker_Chunk: H_Worker_Chunk(self, e->u.h_Chunk.v_lo, e->u.h_Chunk.v_hi, e->u.h_Chunk.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Result: H_Main_Result(self, e->u.h_Result.v_part); break;
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
    a->v_got = INT64_C(0);
    a->v_total = INT64_C(0);
    a->v_t0 = INT64_C(0);
    a->v_serial = INT64_C(0);
    a->v_nworkers = INT64_C(64);
    a->v_span = INT64_C(200000000);
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
