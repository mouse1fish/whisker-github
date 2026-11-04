/* 由 whiskerc 生成的 C 代码（源文件：ordering.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Verifier {
    WhiskerActor base;
    int64_t v_expect;
    int64_t v_got;
    int64_t v_bad;
    WhiskerActor* v_hub;
} A_Verifier;

typedef struct A_Main {
    WhiskerActor base;
    WhiskerActor* v_v;
} A_Main;

typedef struct M_Verifier_Setup { WhiskerActor* v_h; } M_Verifier_Setup;
typedef struct M_Verifier_Tick { int64_t v_n; } M_Verifier_Tick;
typedef struct M_Verifier_Verify { int32_t _unused; } M_Verifier_Verify;
enum { T_Verifier_Setup = 1, T_Verifier_Tick = 2, T_Verifier_Verify = 3 };
typedef struct E_Verifier { int32_t tag; union { M_Verifier_Setup h_Setup; M_Verifier_Tick h_Tick; M_Verifier_Verify h_Verify; } u; } E_Verifier;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Summary { int64_t v_got; int64_t v_bad; int64_t v_expect; } M_Main_Summary;
enum { T_Main_Start = 1, T_Main_Summary = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Summary h_Summary; } u; } E_Main;

static void D_Verifier(WhiskerActor* a, void* payload);
static A_Verifier* N_Verifier(void);
static void H_Verifier_Setup(A_Verifier* self, WhiskerActor* v_h);
static void H_Verifier_Tick(A_Verifier* self, int64_t v_n);
static void H_Verifier_Verify(A_Verifier* self);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Summary(A_Main* self, int64_t v_got, int64_t v_bad, int64_t v_expect);

static void H_Verifier_Setup(A_Verifier* self, WhiskerActor* v_h) {
    self->v_hub = v_h;
}

static void H_Verifier_Tick(A_Verifier* self, int64_t v_n) {
    self->v_got = (self->v_got + INT64_C(1));
    if ((v_n != self->v_expect)) {
        self->v_bad = (self->v_bad + INT64_C(1));
    }
    self->v_expect = (v_n + INT64_C(1));
}

static void H_Verifier_Verify(A_Verifier* self) {
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Summary;
        _e1->u.h_Summary.v_got = self->v_got;
        _e1->u.h_Summary.v_bad = self->v_bad;
        _e1->u.h_Summary.v_expect = self->v_expect;
        whisker_send((WhiskerActor*)(self->v_hub), _e1);
    }
}

static void H_Main_Start(A_Main* self) {
    self->v_v = ((WhiskerActor*)N_Verifier());
    {
        E_Verifier* _e2 = (E_Verifier*)whisker_msg_new(sizeof(E_Verifier));
        _e2->tag = T_Verifier_Setup;
        _e2->u.h_Setup.v_h = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(self->v_v), _e2);
    }
    int64_t v_i = INT64_C(0);
    while ((v_i < INT64_C(100000))) {
        {
            E_Verifier* _e3 = (E_Verifier*)whisker_msg_new(sizeof(E_Verifier));
            _e3->tag = T_Verifier_Tick;
            _e3->u.h_Tick.v_n = v_i;
            whisker_send((WhiskerActor*)(self->v_v), _e3);
        }
        v_i = (v_i + INT64_C(1));
    }
    {
        E_Verifier* _e4 = (E_Verifier*)whisker_msg_new(sizeof(E_Verifier));
        _e4->tag = T_Verifier_Verify;
        whisker_send((WhiskerActor*)(self->v_v), _e4);
    }
}

static void H_Main_Summary(A_Main* self, int64_t v_got, int64_t v_bad, int64_t v_expect) {
    whisker_print_begin();
    whisker_print_str("收到 ");
    whisker_print_int(v_got);
    whisker_print_str(" 条 | 序号错乱 ");
    whisker_print_int(v_bad);
    whisker_print_str(" 条 | 期望下一条 ");
    whisker_print_int(v_expect);
    whisker_print_end();
}

static void D_Verifier(WhiskerActor* a, void* payload) {
    A_Verifier* self = (A_Verifier*)a;
    E_Verifier* e = (E_Verifier*)payload;
    switch (e->tag) {
    case T_Verifier_Setup: H_Verifier_Setup(self, e->u.h_Setup.v_h); break;
    case T_Verifier_Tick: H_Verifier_Tick(self, e->u.h_Tick.v_n); break;
    case T_Verifier_Verify: H_Verifier_Verify(self); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Summary: H_Main_Summary(self, e->u.h_Summary.v_got, e->u.h_Summary.v_bad, e->u.h_Summary.v_expect); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Verifier* N_Verifier(void) {
    A_Verifier* a = (A_Verifier*)whisker_actor_new("Verifier", sizeof(A_Verifier), D_Verifier);
    a->v_expect = INT64_C(0);
    a->v_got = INT64_C(0);
    a->v_bad = INT64_C(0);
    a->v_hub = NULL;
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_v = NULL;
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
