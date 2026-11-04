/* 由 whiskerc 生成的 C 代码（源文件：hello.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Main {
    WhiskerActor base;
} A_Main;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
enum { T_Main_Start = 1 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; } u; } E_Main;

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);

static void H_Main_Start(A_Main* self) {
    whisker_print_begin();
    whisker_print_str("你好，Whisker！");
    whisker_print_end();
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    default: break;
    }
    whisker_msg_free(e);
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
