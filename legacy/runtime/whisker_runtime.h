/*
 * whisker_runtime.h —— Whisker 语言 Actor 运行时（M0）
 *
 * 设计要点：
 *   1. Actor = 私有状态 + 邮箱（mailbox）+ 消息处理函数（dispatch）
 *   2. Actor 之间不共享可变内存，只能通过消息通信 → 数据竞争在语言层面不可能发生
 *   3. 调度器：M:N（N 个工作线程跑 M 个 Actor），Actor 是调度单位而非线程
 *   4. 静止检测：所有邮箱为空且无 Actor 在运行 → 调度器返回
 *
 * M0 已知取舍（M1 处理）：
 *   - 全局调度锁（粗粒度，先保证正确性；后续换分片锁 / 无锁队列）
 *   - Actor 生命周期：M0 不回收单个 Actor（进程退出时统一释放）
 */
#ifndef WHISKER_RUNTIME_H
#define WHISKER_RUNTIME_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct WhiskerActor WhiskerActor;
typedef void (*WhiskerDispatchFn)(WhiskerActor* self, void* payload);

/* 邮箱节点（消息按到达顺序 FIFO 处理） */
typedef struct WhiskerMsgNode {
    void* payload;
    struct WhiskerMsgNode* next;
} WhiskerMsgNode;

/* 调度状态 */
enum {
    WHISKER_IDLE    = 0,  /* 邮箱空、不在就绪队列 */
    WHISKER_QUEUED  = 1,  /* 在就绪队列等待工作线程 */
    WHISKER_RUNNING = 2   /* 正被某个工作线程处理 */
};

/* Actor 头。生成代码里的每个 actor 结构体都必须把本结构体作为第一个成员。 */
struct WhiskerActor {
    const char*     name;
    WhiskerDispatchFn  dispatch;
    int             state;
    WhiskerMsgNode*    head;    /* 邮箱头 */
    WhiskerMsgNode*    tail;    /* 邮箱尾 */
    WhiskerActor*      qnext;   /* 就绪队列链 */
};

/* ---- 生命周期 ---- */
void       whisker_runtime_init(int workers);   /* workers <= 0 → 自动取逻辑核数 */
void       whisker_runtime_shutdown(void);
WhiskerActor* whisker_actor_new(const char* name, size_t size, WhiskerDispatchFn fn);
int        whisker_cores(void);

/* ---- 消息 ---- */
void* whisker_msg_new(size_t size);            /* 分配消息信封（零初始化） */
void  whisker_msg_free(void* p);
void  whisker_send(WhiskerActor* target, void* payload);  /* 所有权转移给接收方 */

/* ---- 调度 ---- */
void   whisker_sched_run(void);      /* 阻塞直到系统静止（无待处理消息） */
double whisker_now_ms(void);
void   whisker_stats(void);          /* 打印运行时统计（WHISKER_STATS=1 时自动调用） */

/* ---- 输出（每个 print 语句在运行时的表现是原子的） ---- */
void whisker_print_begin(void);
void whisker_print_int(int64_t v);
void whisker_print_bool(bool v);
void whisker_print_str(const char* s);
void whisker_print_end(void);

#ifdef __cplusplus
}
#endif
#endif /* WHISKER_RUNTIME_H */
