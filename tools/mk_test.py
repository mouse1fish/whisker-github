# -*- coding: utf-8 -*-
"""把指定测试源码写入 build/lex_input.txt。用法: python tools/mk_test.py m1|m2|m3"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = {
"m1": '''actor Main {
    on Start {
        total: Int = 0
        for i in 0 .. 10 {
            total = total + i * 2
        }
        print(total)
        if total == 90 {
            print("eq-ok")
        } else {
            print("eq-bad")
        }
        j: Int = 3
        while j > 0 {
            j = j - 1
        }
        print(j)
        print(total % 7)
        print(total / 20)
        print(-total / 20)
    }
}
''',
"m2": '''actor Main {
    on Start {
        s: Str = strCat("ab", "cd")
        print(s)
        print(strLen(s))
        print(intToStr(42))
        n: Int = strToInt("17")
        print(n + 5)
        if s == "abcd" {
            print("seq-ok")
        }
        if s == "abce" {
            print("seq-bad")
        }
        print(square(9))
        print(greet("Whisker"))
    }
    def square[x: Int] -> Int {
        return x * x
    }
    def greet[name: Str] -> Str {
        return strCat("hi,", name)
    }
}
''',
"m3": '''actor Main {
    count: Int = 7
    buf: Int[4]
    on Start {
        print(count)
        count = count + 1
        print(count)
        buf[0] = 10
        buf[3] = 33
        print(buf[0] + buf[3])
        k: Int = 0
        sum: Int = 0
        for k in 0 .. 4 {
            sum = sum + buf[k]
        }
        print(sum)
    }
}
''',
}
name = sys.argv[1] if len(sys.argv) > 1 else "m1"
(ROOT / "build" / "lex_input.txt").write_text(SRC[name], encoding="utf-8")
print(f"lex_input.txt <- {name}")
