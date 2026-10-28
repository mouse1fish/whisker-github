"""Whisker 类型系统

类型：
  Int / Bool / Str / ActorRef[X]          标量（各占 8 字节）
  T[N]                                    固定长度数组（元素是标量，连续存放，每个元素 8 字节）

数组语义（M1）：
  - 数组是「值」：直接嵌在 actor 字段区或栈帧里，不额外分配
  - 不能整体赋值（`a = b` 对数组是编译期错误）
  - 作为参数传递时按**引用**传（传的是基地址，像 C 的数组退化为指针）——文件读写等内置要用
  - 下标访问带边界检查，越界会打印错误并退出
"""
from __future__ import annotations

INT = "Int"
BOOL = "Bool"
STR = "Str"
VOID = "Void"
ACTORREF = "ActorRef"
ARRAY = "Array"
PTR = "Ptr"                    # 底层指针（不可空性靠 isNull 检查；不参与消息传递）
ERROR = "<error>"

SCALARS = (INT, BOOL, STR, ACTORREF, PTR)


class Ty:
    __slots__ = ("kind", "arg", "size")

    def __init__(self, kind: str, arg=None, size: int | None = None) -> None:
        self.kind = kind
        self.arg = arg          # ActorRef<X> 的 X（str）；数组的元素类型（Ty）
        self.size = size        # 数组长度

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Ty)
                and self.kind == other.kind
                and self.arg == other.arg
                and self.size == other.size)

    def __hash__(self) -> int:
        return hash((self.kind, str(self.arg), self.size))

    def __str__(self) -> str:
        if self.kind == ACTORREF:
            return f"ActorRef[{self.arg}]"
        if self.kind == ARRAY:
            return f"{self.arg}[{self.size}]"
        return self.kind

    @property
    def is_error(self) -> bool:
        return self.kind == ERROR

    @property
    def is_actorref(self) -> bool:
        return self.kind == ACTORREF

    @property
    def is_array(self) -> bool:
        return self.kind == ARRAY

    @property
    def is_ptr(self) -> bool:
        return self.kind == PTR

    @property
    def is_scalar(self) -> bool:
        return self.kind in SCALARS

    @property
    def elem(self) -> "Ty":
        assert self.kind == ARRAY
        return self.arg

    def byte_size(self) -> int:
        """该类型占多少字节（元素统一 8 字节）"""
        return 8 * self.size if self.kind == ARRAY else 8

    def c_type(self) -> str:
        if self.kind == INT:
            return "int64_t"
        if self.kind == BOOL:
            return "bool"
        if self.kind == STR:
            return "const char*"
        if self.kind == VOID:
            return "void"
        if self.kind == ACTORREF:
            return "WhiskerActor*"
        raise AssertionError(f"无法映射到 C 类型: {self.kind}")

    def print_fn(self) -> str | None:
        return {INT: "whisker_print_int", BOOL: "whisker_print_bool", STR: "whisker_print_str"}.get(self.kind)


INT_TY = Ty(INT)
BOOL_TY = Ty(BOOL)
STR_TY = Ty(STR)
VOID_TY = Ty(VOID)
PTR_TY = Ty(PTR)
ERROR_TY = Ty(ERROR)


def actorref(name: str) -> Ty:
    return Ty(ACTORREF, name)


def array_of(elem: Ty, size: int) -> Ty:
    return Ty(ARRAY, elem, size)


def parse_type_name(name: str, arg: str | None = None) -> Ty | None:
    """把源代码里的类型写法转成 Ty；无法识别返回 None"""
    if name == "Int" and arg is None:
        return INT_TY
    if name == "Bool" and arg is None:
        return BOOL_TY
    if name == "Str" and arg is None:
        return STR_TY
    if name == "Ptr" and arg is None:
        return PTR_TY
    if name == "ActorRef" and arg is not None:
        return actorref(arg)
    return None