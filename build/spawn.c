/* 由 whiskerc 生成的 C 代码（源文件：spawn.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Child {
    WhiskerActor base;
    int64_t v_got;
} A_Child;

typedef struct A_Main {
    WhiskerActor base;
    int64_t v_total;
} A_Main;

typedef struct M_Child_Ping { WhiskerActor* v_reply; } M_Child_Ping;
enum { T_Child_Ping = 1 };
typedef struct E_Child { int32_t tag; union { M_Child_Ping h_Ping; } u; } E_Child;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Pong { int64_t v_v; } M_Main_Pong;
enum { T_Main_Start = 1, T_Main_Pong = 2 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Pong h_Pong; } u; } E_Main;

static void D_Child(WhiskerActor* a, void* payload);
static A_Child* N_Child(void);
static void H_Child_Ping(A_Child* self, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Pong(A_Main* self, int64_t v_v);

static void H_Child_Ping(A_Child* self, WhiskerActor* v_reply) {
    self->v_got = (self->v_got + INT64_C(1));
    {
        E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e1->tag = T_Main_Pong;
        _e1->u.h_Pong.v_v = self->v_got;
        whisker_send((WhiskerActor*)(v_reply), _e1);
    }
}

static void H_Main_Start(A_Main* self) {
    WhiskerActor* v_c = ((WhiskerActor*)N_Child());
    {
        E_Child* _e2 = (E_Child*)whisker_msg_new(sizeof(E_Child));
        _e2->tag = T_Child_Ping;
        _e2->u.h_Ping.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(v_c), _e2);
    }
    {
        E_Child* _e3 = (E_Child*)whisker_msg_new(sizeof(E_Child));
        _e3->tag = T_Child_Ping;
        _e3->u.h_Ping.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(v_c), _e3);
    }
    {
        E_Child* _e4 = (E_Child*)whisker_msg_new(sizeof(E_Child));
        _e4->tag = T_Child_Ping;
        _e4->u.h_Ping.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(v_c), _e4);
    }
}

static void H_Main_Pong(A_Main* self, int64_t v_v) {
    self->v_total = (self->v_total + v_v);
    whisker_print_begin();
    whisker_print_str("收到 Pong(");
    whisker_print_int(v_v);
    whisker_print_str(") 累计 ");
    whisker_print_int(self->v_total);
    whisker_print_end();
}

static void D_Child(WhiskerActor* a, void* payload) {
    A_Child* self = (A_Child*)a;
    E_Child* e = (E_Child*)payload;
    switch (e->tag) {
    case T_Child_Ping: H_Child_Ping(self, e->u.h_Ping.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Pong: H_Main_Pong(self, e->u.h_Pong.v_v); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Child* N_Child(void) {
    A_Child* a = (A_Child*)whisker_actor_new("Child", sizeof(A_Child), D_Child);
    a->v_got = INT64_C(0);
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_total = INT64_C(0);
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
