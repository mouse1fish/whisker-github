/* 由 whiskerc 生成的 C 代码（源文件：counter.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Counter {
    WhiskerActor base;
    int64_t v_total;
} A_Counter;

typedef struct A_Main {
    WhiskerActor base;
} A_Main;

typedef struct M_Counter_Inc { int64_t v_n; } M_Counter_Inc;
typedef struct M_Counter_Get { WhiskerActor* v_reply; } M_Counter_Get;
enum { T_Counter_Inc = 1, T_Counter_Get = 2 };
typedef struct E_Counter { int32_t tag; union { M_Counter_Inc h_Inc; M_Counter_Get h_Get; } u; } E_Counter;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Report { int64_t v_total; } M_Main_Report;
enum { T_Main_Start = 1, T_Main_Report = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Report h_Report; } u; } E_Main;

static void D_Counter(WhiskerActor* a, void* payload);
static A_Counter* N_Counter(void);
static void H_Counter_Inc(A_Counter* self, int64_t v_n);
static void H_Counter_Get(A_Counter* self, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Report(A_Main* self, int64_t v_total);

static void H_Counter_Inc(A_Counter* self, int64_t v_n) {
    self->v_total = (self->v_total + v_n);
}

static void H_Counter_Get(A_Counter* self, WhiskerActor* v_reply) {
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Report;
        _e1->u.h_Report.v_total = self->v_total;
        whisker_send((WhiskerActor*)(v_reply), _e1);
    }
}

static void H_Main_Start(A_Main* self) {
    WhiskerActor* v_c = ((WhiskerActor*)N_Counter());
    {
        E_Counter* _e2 = (E_Counter*)whisker_msg_new(sizeof(E_Counter));
        _e2->tag = T_Counter_Inc;
        _e2->u.h_Inc.v_n = INT64_C(3);
        whisker_send((WhiskerActor*)(v_c), _e2);
    }
    {
        E_Counter* _e3 = (E_Counter*)whisker_msg_new(sizeof(E_Counter));
        _e3->tag = T_Counter_Inc;
        _e3->u.h_Inc.v_n = INT64_C(4);
        whisker_send((WhiskerActor*)(v_c), _e3);
    }
    {
        E_Counter* _e4 = (E_Counter*)whisker_msg_new(sizeof(E_Counter));
        _e4->tag = T_Counter_Inc;
        _e4->u.h_Inc.v_n = INT64_C(35);
        whisker_send((WhiskerActor*)(v_c), _e4);
    }
    {
        E_Counter* _e5 = (E_Counter*)whisker_msg_new(sizeof(E_Counter));
        _e5->tag = T_Counter_Get;
        _e5->u.h_Get.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(v_c), _e5);
    }
}

static void H_Main_Report(A_Main* self, int64_t v_total) {
    whisker_print_begin();
    whisker_print_str("Counter 累加结果 = ");
    whisker_print_int(v_total);
    whisker_print_end();
}

static void D_Counter(WhiskerActor* a, void* payload) {
    A_Counter* self = (A_Counter*)a;
    E_Counter* e = (E_Counter*)payload;
    switch (e->tag) {
    case T_Counter_Inc: H_Counter_Inc(self, e->u.h_Inc.v_n); break;
    case T_Counter_Get: H_Counter_Get(self, e->u.h_Get.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Report: H_Main_Report(self, e->u.h_Report.v_total); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Counter* N_Counter(void) {
    A_Counter* a = (A_Counter*)whisker_actor_new("Counter", sizeof(A_Counter), D_Counter);
    a->v_total = INT64_C(0);
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
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
