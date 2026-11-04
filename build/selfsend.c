/* 由 whiskerc 生成的 C 代码（源文件：selfsend.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Main {
    WhiskerActor base;
    int64_t v_n;
} A_Main;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Bump { int64_t v_step; int64_t v_left; } M_Main_Bump;
enum { T_Main_Start = 1, T_Main_Bump = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Bump h_Bump; } u; } E_Main;

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Bump(A_Main* self, int64_t v_step, int64_t v_left);

static void H_Main_Start(A_Main* self) {
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Bump;
        _e1->u.h_Bump.v_step = INT64_C(1);
        _e1->u.h_Bump.v_left = INT64_C(100);
        whisker_send((WhiskerActor*)(((WhiskerActor*)self)), _e1);
    }
}

static void H_Main_Bump(A_Main* self, int64_t v_step, int64_t v_left) {
    self->v_n = (self->v_n + v_step);
    if ((v_left > INT64_C(0))) {
        {
            E_Main* _e2 = (E_Main*)whisker_msg_new(sizeof(E_Main));
            _e2->tag = T_Main_Bump;
            _e2->u.h_Bump.v_step = (v_step + INT64_C(1));
            _e2->u.h_Bump.v_left = (v_left - INT64_C(1));
            whisker_send((WhiskerActor*)(((WhiskerActor*)self)), _e2);
        }
    } else {
        whisker_print_begin();
        whisker_print_str("累加完成 n = ");
        whisker_print_int(self->v_n);
        whisker_print_end();
    }
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Bump: H_Main_Bump(self, e->u.h_Bump.v_step, e->u.h_Bump.v_left); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_n = INT64_C(0);
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
