/* 由 whiskerc 生成的 C 代码（源文件：pingpong.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Player {
    WhiskerActor base;
    WhiskerActor* v_peer;
    WhiskerActor* v_hub;
    int64_t v_hops;
} A_Player;

typedef struct A_Main {
    WhiskerActor base;
    WhiskerActor* v_a;
    WhiskerActor* v_b;
    int64_t v_reports;
    int64_t v_sum;
} A_Main;

typedef struct M_Player_Connect { WhiskerActor* v_p; WhiskerActor* v_h; } M_Player_Connect;
typedef struct M_Player_Hop { int64_t v_n; int64_t v_left; } M_Player_Hop;
typedef struct M_Player_Ask { WhiskerActor* v_reply; } M_Player_Ask;
enum { T_Player_Connect = 1, T_Player_Hop = 2, T_Player_Ask = 3 };
typedef struct E_Player { int32_t tag; union { M_Player_Connect h_Connect; M_Player_Hop h_Hop; M_Player_Ask h_Ask; } u; } E_Player;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Finished { int64_t v_last; } M_Main_Finished;
typedef struct M_Main_Report { int64_t v_hops; } M_Main_Report;
enum { T_Main_Start = 1, T_Main_Finished = 2, T_Main_Report = 3 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Finished h_Finished; M_Main_Report h_Report; } u; } E_Main;

static void D_Player(WhiskerActor* a, void* payload);
static A_Player* N_Player(void);
static void H_Player_Connect(A_Player* self, WhiskerActor* v_p, WhiskerActor* v_h);
static void H_Player_Hop(A_Player* self, int64_t v_n, int64_t v_left);
static void H_Player_Ask(A_Player* self, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Finished(A_Main* self, int64_t v_last);
static void H_Main_Report(A_Main* self, int64_t v_hops);

static void H_Player_Connect(A_Player* self, WhiskerActor* v_p, WhiskerActor* v_h) {
    self->v_peer = v_p;
    self->v_hub = v_h;
}

static void H_Player_Hop(A_Player* self, int64_t v_n, int64_t v_left) {
    self->v_hops = (self->v_hops + INT64_C(1));
    if ((v_left > INT64_C(0))) {
        {
            E_Player* _e1 = (E_Player*)whisker_msg_new(sizeof(E_Player));
            _e1->tag = T_Player_Hop;
            _e1->u.h_Hop.v_n = (v_n + INT64_C(1));
            _e1->u.h_Hop.v_left = (v_left - INT64_C(1));
            whisker_send((WhiskerActor*)(self->v_peer), _e1);
        }
    } else {
        {
            E_Main* _e2 = (E_Main*)whisker_msg_new(sizeof(E_Main));
            _e2->tag = T_Main_Finished;
            _e2->u.h_Finished.v_last = v_n;
            whisker_send((WhiskerActor*)(self->v_hub), _e2);
        }
    }
}

static void H_Player_Ask(A_Player* self, WhiskerActor* v_reply) {
    {
        E_Main* _e3 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e3->tag = T_Main_Report;
        _e3->u.h_Report.v_hops = self->v_hops;
        whisker_send((WhiskerActor*)(v_reply), _e3);
    }
}

static void H_Main_Start(A_Main* self) {
    self->v_a = ((WhiskerActor*)N_Player());
    self->v_b = ((WhiskerActor*)N_Player());
    {
        E_Player* _e4 = (E_Player*)whisker_msg_new(sizeof(E_Player));
        _e4->tag = T_Player_Connect;
        _e4->u.h_Connect.v_p = self->v_b;
        _e4->u.h_Connect.v_h = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(self->v_a), _e4);
    }
    {
        E_Player* _e5 = (E_Player*)whisker_msg_new(sizeof(E_Player));
        _e5->tag = T_Player_Connect;
        _e5->u.h_Connect.v_p = self->v_a;
        _e5->u.h_Connect.v_h = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(self->v_b), _e5);
    }
    {
        E_Player* _e6 = (E_Player*)whisker_msg_new(sizeof(E_Player));
        _e6->tag = T_Player_Hop;
        _e6->u.h_Hop.v_n = INT64_C(1);
        _e6->u.h_Hop.v_left = INT64_C(200000);
        whisker_send((WhiskerActor*)(self->v_a), _e6);
    }
}

static void H_Main_Finished(A_Main* self, int64_t v_last) {
    whisker_print_begin();
    whisker_print_str("链条结束，最后一跳编号 = ");
    whisker_print_int(v_last);
    whisker_print_end();
    {
        E_Player* _e7 = (E_Player*)whisker_msg_new(sizeof(E_Player));
        _e7->tag = T_Player_Ask;
        _e7->u.h_Ask.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(self->v_a), _e7);
    }
    {
        E_Player* _e8 = (E_Player*)whisker_msg_new(sizeof(E_Player));
        _e8->tag = T_Player_Ask;
        _e8->u.h_Ask.v_reply = ((WhiskerActor*)self);
        whisker_send((WhiskerActor*)(self->v_b), _e8);
    }
}

static void H_Main_Report(A_Main* self, int64_t v_hops) {
    self->v_reports = (self->v_reports + INT64_C(1));
    self->v_sum = (self->v_sum + v_hops);
    if ((self->v_reports == INT64_C(2))) {
        whisker_print_begin();
        whisker_print_str("两方累计跳数 = ");
        whisker_print_int(self->v_sum);
        whisker_print_str("（期望 200001）");
        whisker_print_end();
    }
}

static void D_Player(WhiskerActor* a, void* payload) {
    A_Player* self = (A_Player*)a;
    E_Player* e = (E_Player*)payload;
    switch (e->tag) {
    case T_Player_Connect: H_Player_Connect(self, e->u.h_Connect.v_p, e->u.h_Connect.v_h); break;
    case T_Player_Hop: H_Player_Hop(self, e->u.h_Hop.v_n, e->u.h_Hop.v_left); break;
    case T_Player_Ask: H_Player_Ask(self, e->u.h_Ask.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Finished: H_Main_Finished(self, e->u.h_Finished.v_last); break;
    case T_Main_Report: H_Main_Report(self, e->u.h_Report.v_hops); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Player* N_Player(void) {
    A_Player* a = (A_Player*)whisker_actor_new("Player", sizeof(A_Player), D_Player);
    a->v_peer = NULL;
    a->v_hub = NULL;
    a->v_hops = INT64_C(0);
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_a = NULL;
    a->v_b = NULL;
    a->v_reports = INT64_C(0);
    a->v_sum = INT64_C(0);
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
