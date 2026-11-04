/* 由 whiskerc 生成的 C 代码（源文件：bank.whisker） */
/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */

#include "whisker_runtime.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct A_Account {
    WhiskerActor base;
    int64_t v_balance;
    WhiskerActor* v_hub;
} A_Account;

typedef struct A_Main {
    WhiskerActor base;
    WhiskerActor* v_a;
    WhiskerActor* v_b;
    WhiskerActor* v_c;
    int64_t v_seed;
    int64_t v_outcomes;
    int64_t v_successes;
    int64_t v_deposits_done;
    bool v_asked;
    int64_t v_reports;
    int64_t v_total;
} A_Main;

typedef struct M_Account_Open { WhiskerActor* v_h; int64_t v_initial; } M_Account_Open;
typedef struct M_Account_TransferTo { WhiskerActor* v_target; int64_t v_n; } M_Account_TransferTo;
typedef struct M_Account_Deposit { int64_t v_n; } M_Account_Deposit;
typedef struct M_Account_Ask { WhiskerActor* v_reply; } M_Account_Ask;
enum { T_Account_Open = 1, T_Account_TransferTo = 2, T_Account_Deposit = 3, T_Account_Ask = 4 };
typedef struct E_Account { int32_t tag; union { M_Account_Open h_Open; M_Account_TransferTo h_TransferTo; M_Account_Deposit h_Deposit; M_Account_Ask h_Ask; } u; } E_Account;

typedef struct M_Main_Start { int32_t _unused; } M_Main_Start;
typedef struct M_Main_Moved { int64_t v_n; } M_Main_Moved;
typedef struct M_Main_Rejected { int32_t _unused; } M_Main_Rejected;
typedef struct M_Main_Deposited { int32_t _unused; } M_Main_Deposited;
typedef struct M_Main_Balance { int64_t v_v; } M_Main_Balance;
typedef struct M_Main_Check { int32_t _unused; } M_Main_Check;
enum { T_Main_Start = 1, T_Main_Moved = 2, T_Main_Rejected = 3, T_Main_Deposited = 4, T_Main_Balance = 5, T_Main_Check = 6 };
typedef struct E_Main { int32_t tag; union { M_Main_Start h_Start; M_Main_Moved h_Moved; M_Main_Rejected h_Rejected; M_Main_Deposited h_Deposited; M_Main_Balance h_Balance; M_Main_Check h_Check; } u; } E_Main;

static void D_Account(WhiskerActor* a, void* payload);
static A_Account* N_Account(void);
static void H_Account_Open(A_Account* self, WhiskerActor* v_h, int64_t v_initial);
static void H_Account_TransferTo(A_Account* self, WhiskerActor* v_target, int64_t v_n);
static void H_Account_Deposit(A_Account* self, int64_t v_n);
static void H_Account_Ask(A_Account* self, WhiskerActor* v_reply);

static void D_Main(WhiskerActor* a, void* payload);
static A_Main* N_Main(void);
static void H_Main_Start(A_Main* self);
static void H_Main_Moved(A_Main* self, int64_t v_n);
static void H_Main_Rejected(A_Main* self);
static void H_Main_Deposited(A_Main* self);
static void H_Main_Balance(A_Main* self, int64_t v_v);
static void H_Main_Check(A_Main* self);

static void H_Account_Open(A_Account* self, WhiskerActor* v_h, int64_t v_initial) {
    self->v_hub = v_h;
    self->v_balance = v_initial;
}

static void H_Account_TransferTo(A_Account* self, WhiskerActor* v_target, int64_t v_n) {
    if ((v_n > self->v_balance)) {
        {
            E_Main* _e1 = (E_Main*)whisker_msg_new(sizeof(E_Main));
            _e1->tag = T_Main_Rejected;
            whisker_send((WhiskerActor*)(self->v_hub), _e1);
        }
    } else {
        self->v_balance = (self->v_balance - v_n);
        {
            E_Account* _e2 = (E_Account*)whisker_msg_new(sizeof(E_Account));
            _e2->tag = T_Account_Deposit;
            _e2->u.h_Deposit.v_n = v_n;
            whisker_send((WhiskerActor*)(v_target), _e2);
        }
        {
            E_Main* _e3 = (E_Main*)whisker_msg_new(sizeof(E_Main));
            _e3->tag = T_Main_Moved;
            _e3->u.h_Moved.v_n = v_n;
            whisker_send((WhiskerActor*)(self->v_hub), _e3);
        }
    }
}

static void H_Account_Deposit(A_Account* self, int64_t v_n) {
    self->v_balance = (self->v_balance + v_n);
    {
        E_Main* _e4 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e4->tag = T_Main_Deposited;
        whisker_send((WhiskerActor*)(self->v_hub), _e4);
    }
}

static void H_Account_Ask(A_Account* self, WhiskerActor* v_reply) {
    {
        E_Main* _e5 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e5->tag = T_Main_Balance;
        _e5->u.h_Balance.v_v = self->v_balance;
        whisker_send((WhiskerActor*)(v_reply), _e5);
    }
}

static void H_Main_Start(A_Main* self) {
    self->v_a = ((WhiskerActor*)N_Account());
    self->v_b = ((WhiskerActor*)N_Account());
    self->v_c = ((WhiskerActor*)N_Account());
    {
        E_Account* _e6 = (E_Account*)whisker_msg_new(sizeof(E_Account));
        _e6->tag = T_Account_Open;
        _e6->u.h_Open.v_h = ((WhiskerActor*)self);
        _e6->u.h_Open.v_initial = INT64_C(1000);
        whisker_send((WhiskerActor*)(self->v_a), _e6);
    }
    {
        E_Account* _e7 = (E_Account*)whisker_msg_new(sizeof(E_Account));
        _e7->tag = T_Account_Open;
        _e7->u.h_Open.v_h = ((WhiskerActor*)self);
        _e7->u.h_Open.v_initial = INT64_C(2000);
        whisker_send((WhiskerActor*)(self->v_b), _e7);
    }
    {
        E_Account* _e8 = (E_Account*)whisker_msg_new(sizeof(E_Account));
        _e8->tag = T_Account_Open;
        _e8->u.h_Open.v_h = ((WhiskerActor*)self);
        _e8->u.h_Open.v_initial = INT64_C(3000);
        whisker_send((WhiskerActor*)(self->v_c), _e8);
    }
    int64_t v_i = INT64_C(0);
    while ((v_i < INT64_C(20000))) {
        self->v_seed = (((self->v_seed * INT64_C(1103515245)) + INT64_C(12345)) % INT64_C(2147483648));
        int64_t v_amount = (self->v_seed % INT64_C(400));
        int64_t v_pick = (self->v_seed % INT64_C(3));
        if ((v_pick == INT64_C(0))) {
            {
                E_Account* _e9 = (E_Account*)whisker_msg_new(sizeof(E_Account));
                _e9->tag = T_Account_TransferTo;
                _e9->u.h_TransferTo.v_target = self->v_b;
                _e9->u.h_TransferTo.v_n = v_amount;
                whisker_send((WhiskerActor*)(self->v_a), _e9);
            }
        } else {
            if ((v_pick == INT64_C(1))) {
                {
                    E_Account* _e10 = (E_Account*)whisker_msg_new(sizeof(E_Account));
                    _e10->tag = T_Account_TransferTo;
                    _e10->u.h_TransferTo.v_target = self->v_c;
                    _e10->u.h_TransferTo.v_n = v_amount;
                    whisker_send((WhiskerActor*)(self->v_b), _e10);
                }
            } else {
                {
                    E_Account* _e11 = (E_Account*)whisker_msg_new(sizeof(E_Account));
                    _e11->tag = T_Account_TransferTo;
                    _e11->u.h_TransferTo.v_target = self->v_a;
                    _e11->u.h_TransferTo.v_n = v_amount;
                    whisker_send((WhiskerActor*)(self->v_c), _e11);
                }
            }
        }
        v_i = (v_i + INT64_C(1));
    }
}

static void H_Main_Moved(A_Main* self, int64_t v_n) {
    self->v_outcomes = (self->v_outcomes + INT64_C(1));
    self->v_successes = (self->v_successes + INT64_C(1));
    {
        E_Main* _e12 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e12->tag = T_Main_Check;
        whisker_send((WhiskerActor*)(((WhiskerActor*)self)), _e12);
    }
}

static void H_Main_Rejected(A_Main* self) {
    self->v_outcomes = (self->v_outcomes + INT64_C(1));
    {
        E_Main* _e13 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e13->tag = T_Main_Check;
        whisker_send((WhiskerActor*)(((WhiskerActor*)self)), _e13);
    }
}

static void H_Main_Deposited(A_Main* self) {
    self->v_deposits_done = (self->v_deposits_done + INT64_C(1));
    {
        E_Main* _e14 = (E_Main*)whisker_msg_new(sizeof(E_Main));
        _e14->tag = T_Main_Check;
        whisker_send((WhiskerActor*)(((WhiskerActor*)self)), _e14);
    }
}

static void H_Main_Balance(A_Main* self, int64_t v_v) {
    self->v_reports = (self->v_reports + INT64_C(1));
    self->v_total = (self->v_total + v_v);
    if ((self->v_reports == INT64_C(3))) {
        whisker_print_begin();
        whisker_print_str("三账户总额 = ");
        whisker_print_int(self->v_total);
        whisker_print_str("（期望 6000）");
        whisker_print_end();
        whisker_print_begin();
        whisker_print_str("转账 20000 笔，成功 ");
        whisker_print_int(self->v_successes);
        whisker_print_str(" 笔，余额不足被拒 ");
        whisker_print_int((self->v_outcomes - self->v_successes));
        whisker_print_str(" 笔");
        whisker_print_end();
    }
}

static void H_Main_Check(A_Main* self) {
    if ((((self->v_outcomes == INT64_C(20000)) && (self->v_deposits_done == self->v_successes)) && (!self->v_asked))) {
        self->v_asked = true;
        {
            E_Account* _e15 = (E_Account*)whisker_msg_new(sizeof(E_Account));
            _e15->tag = T_Account_Ask;
            _e15->u.h_Ask.v_reply = ((WhiskerActor*)self);
            whisker_send((WhiskerActor*)(self->v_a), _e15);
        }
        {
            E_Account* _e16 = (E_Account*)whisker_msg_new(sizeof(E_Account));
            _e16->tag = T_Account_Ask;
            _e16->u.h_Ask.v_reply = ((WhiskerActor*)self);
            whisker_send((WhiskerActor*)(self->v_b), _e16);
        }
        {
            E_Account* _e17 = (E_Account*)whisker_msg_new(sizeof(E_Account));
            _e17->tag = T_Account_Ask;
            _e17->u.h_Ask.v_reply = ((WhiskerActor*)self);
            whisker_send((WhiskerActor*)(self->v_c), _e17);
        }
    }
}

static void D_Account(WhiskerActor* a, void* payload) {
    A_Account* self = (A_Account*)a;
    E_Account* e = (E_Account*)payload;
    switch (e->tag) {
    case T_Account_Open: H_Account_Open(self, e->u.h_Open.v_h, e->u.h_Open.v_initial); break;
    case T_Account_TransferTo: H_Account_TransferTo(self, e->u.h_TransferTo.v_target, e->u.h_TransferTo.v_n); break;
    case T_Account_Deposit: H_Account_Deposit(self, e->u.h_Deposit.v_n); break;
    case T_Account_Ask: H_Account_Ask(self, e->u.h_Ask.v_reply); break;
    default: break;
    }
    whisker_msg_free(e);
}

static void D_Main(WhiskerActor* a, void* payload) {
    A_Main* self = (A_Main*)a;
    E_Main* e = (E_Main*)payload;
    switch (e->tag) {
    case T_Main_Start: H_Main_Start(self); break;
    case T_Main_Moved: H_Main_Moved(self, e->u.h_Moved.v_n); break;
    case T_Main_Rejected: H_Main_Rejected(self); break;
    case T_Main_Deposited: H_Main_Deposited(self); break;
    case T_Main_Balance: H_Main_Balance(self, e->u.h_Balance.v_v); break;
    case T_Main_Check: H_Main_Check(self); break;
    default: break;
    }
    whisker_msg_free(e);
}

static A_Account* N_Account(void) {
    A_Account* a = (A_Account*)whisker_actor_new("Account", sizeof(A_Account), D_Account);
    a->v_balance = INT64_C(0);
    a->v_hub = NULL;
    return a;
}

static A_Main* N_Main(void) {
    A_Main* a = (A_Main*)whisker_actor_new("Main", sizeof(A_Main), D_Main);
    a->v_a = NULL;
    a->v_b = NULL;
    a->v_c = NULL;
    a->v_seed = INT64_C(12345);
    a->v_outcomes = INT64_C(0);
    a->v_successes = INT64_C(0);
    a->v_deposits_done = INT64_C(0);
    a->v_asked = false;
    a->v_reports = INT64_C(0);
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
