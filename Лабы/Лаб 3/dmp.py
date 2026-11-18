import sys

LAMBDA = "λ"
EPS    = "eps"
STEP_LIMIT = 100000


class DMP:
    def __init__(self, states, input_alpha, stack_alpha, start, final, start_stack):
        self.states = list(states)
        self.input_alpha = list(input_alpha)
        self.stack_alpha = list(stack_alpha)
        self.start = start
        self.final = set(final)
        self.start_stack = start_stack
        self.transitions = {}
        self.dup = [] # конфликты одинаковых ключей

    def add(self, q, x, stack, q2, s_state): #добавление перехода, если такой уже был(но с др результатом) - запис. в dup
        key = (q, x, stack)
        if key in self.transitions and self.transitions[key] != (q2, s_state): #тот же ключ, но др.результат
            self.dup.append((key, self.transitions[key], (q2, s_state)))
        self.transitions[key] = (q2, s_state) #сохр переход

    def step(self, state, rest, stack): #rest - текущ строка(остат)
        if not stack: #магазин уже eps
            return None
        top, tail = stack[0], stack[1:] #верх символ магазина и все остальные

        if rest:
            key = (state, rest[0], top) #1симв
            if key in self.transitions:
                q2, s_state = self.transitions[key]
                rule = (state, rest[0], top, q2, s_state) #запом переход
                return q2, rest[1:], s_state + tail, rule #сдвиг головку на след.симв

        key = (state, LAMBDA, top) #для пустого 
        if key in self.transitions:
            q2, s_state = self.transitions[key]
            rule = (state, LAMBDA, top, q2, s_state)
            return q2, rest, s_state + tail, rule

        return None

    def ret_reason(self, state, rest, stack):
        if stack == "" and rest != "":
            return (f"магазин пуст(eps), но входная цепочка содержит символы (остаток '{rest}')")
        if rest == "" and stack != "":
            return (f"входная цепочка прочитана до конца, но магазин не пуст (верхний символ '{stack[0]}')")
        if rest == "" and stack == "" and state not in self.final:
            return (f"входная цепочка прочитана до конца, магазин пуст, но состояние '{state}' не является конечным")
        top = stack[0]
        x = rest[0]
        return (f"нет перехода δ({state}, '{x}', '{top}')")

    def run_process(self, word):
        state, rest, stack = self.start, word, self.start_stack
        trace = [(state, rest, stack, None)]
        seen = set()

        while True:
            if rest == "" and stack == "" and state in self.final: #вход прочитан, магазин пуст, финальное состояние
                return True, "допущена", trace

            key = (state, rest, stack)
            if key in seen:
                return False, "Произошло зацикливание, сосотяние повторилось", trace
            seen.add(key)

            nxt = self.step(state, rest, stack)
            if nxt is None: #такта нет - укажем причину
                return False, self.ret_reason(state, rest, stack), trace

            state, rest, stack, rule = nxt #обновл такт
            trace.append((state, rest, stack, rule))

            if len(trace) > STEP_LIMIT:
                return False, f"Превышен лимит шагов ({STEP_LIMIT})", trace


def parse_file(path):
    with open(path, encoding="utf-8") as f:
        rl = f.readlines()

    lines = []
    for l in rl:
        s = l.rstrip("\n").rstrip("\r")

        lines.append(s)

    while lines and lines[-1].strip() == "":
        lines.pop()

    if len(lines) < 6:
        raise ValueError(f"Недостаточное количество строк в файле: {len(lines)} (нужно ≥ 6)")

    states = lines[0].split()
    input_alpha = lines[1].split()
    stack_alpha = lines[2].split()
    start = lines[3].split()[0]
    final = lines[4].split()
    start_stack = lines[5].split()[0]

    if start not in states:
        raise ValueError(f"начальное состояние '{start}' не входит в Q")
    for f_state in final:
        if f_state not in states:
            raise ValueError(f"конечное состояние '{f_state}' не входит в Q")
    if start_stack not in stack_alpha:
        raise ValueError(f"начальный символ магазина '{start_stack}' не входит в Z_alph")

    transitions, strings = [], []
    for line in lines[6:]:
        if "->" in line:
            left, right = line.split("->", 1)
            parts = left.split()
            if len(parts) != 3:
                raise ValueError(f"Некорректная запись левой части перехода (нужно 'q x stack -> ...'): {line!r}")
            q, x, stack = parts

            if q not in states:
                raise ValueError(f"состояние '{q}' не входит в Q: {line!r}")
            if x != LAMBDA and x not in input_alpha:
                raise ValueError(f"входной символ '{x}' не входит в V: {line!r}")
            if stack not in stack_alpha:
                raise ValueError(f"Символ стека '{stack}' не входит в Z_alph: {line!r}")
            
            if LAMBDA in input_alpha or EPS in input_alpha:
                raise ValueError("λ/eps — служебные обозначения, их нельзя включать в V")
            if LAMBDA in stack_alpha or EPS in stack_alpha:
                raise ValueError("λ/eps — служебные обозначения, их нельзя включать в Z_alph")

            rparts = right.split()
            if not rparts:
                raise ValueError(f"в переходе нет целевого состояния: {line!r}")
            q2 = rparts[0]
            if q2 not in states:
                raise ValueError(f"состояние '{q2}' не входит в Q: {line!r}")

            s_state = "".join(rparts[1:]) if len(rparts) > 1 else "" #склейка пробелов в правой части
            if s_state == EPS:
                s_state = ""
            for ch in s_state:
                if ch not in stack_alpha:
                    raise ValueError(f"символ '{ch}' в магазине не входит в Z_alph: {line!r}")

            transitions.append((q, x, stack, q2, s_state)) #сохр перехода
        else:
            strings.append(line.strip())


    strings = ["" if s == LAMBDA else s for s in strings] #для пустой строки == λ

    if not strings: #или можно не писать строку вообще - тоже самое с лямбдой
        strings = [""]

    return (states, input_alpha, stack_alpha, start, final, start_stack, transitions, strings)


def fstate(s, r, k):
    if not r:
        r = LAMBDA
    if not k:
        k = LAMBDA
    return f"({s}, {r}, {k})"


def format_rule(rule):
    if rule is None:
        return ""
    q, x, top, q2, s_state = rule
    if s_state:
        stack_str = s_state
    else:
        stack_str = EPS
    return f"{q} {x} {top} -> {q2} {stack_str}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "input.txt"

    try:
        (states, input_alpha, stack_alpha, start, final, start_stack, transitions, strings) = parse_file(path)
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return 1

    m = DMP(states, input_alpha, stack_alpha, start, final, start_stack)
    for t in transitions:
        m.add(*t)

    print("ДМП-АВТОМАТ")
    print("-" * 50)
    print(f"Q = {{{', '.join(states)}}}")
    print(f"V = {{{', '.join(input_alpha)}}}")
    print(f"Z_alph = {{{', '.join(stack_alpha)}}}")
    print(f"q0 = {start}")
    print(f"z0 = {start_stack}")
    print(f"F = {{{', '.join(final)}}}")
    print(f"переходов: {len(transitions)}")

    if m.dup:
        print("Ошибка! Одинаковые (q,x,stack) с разными результатами:")
        for key, old, new in m.dup:
            print(f"- δ{key}: {old} и {new}")

    for word in strings:
        print()
        if word == "":
            print("Входная цепочка: ''")
        else:
            print(f"Входная цепочка: {word!r}")
        print("-" * 50)


        ok, reason, trace = m.run_process(word)

        print("Совершаем переходы:")
        for i, (s, r, k, rule) in enumerate(trace):
            
            if i == 0:
                prefix = "начальное:"
            else:
                prefix = f"шаг {i}"
                
            if (ok and i == len(trace) - 1):
                mark = " - цепочка верна"
            else:
                mark = ""
            
            if rule is not None: #если переход не none
                line = f"{prefix}: {fstate(s, r, k)}   [{format_rule(rule)}]{mark}"
            else:
                line = f"{prefix}: {fstate(s, r, k)}{mark}"
            print(line)

        print()
        if ok:
            print("Цепочка принадлежит языку")
        else:
            print("Цепочка не принадлежит языку")
            print(f"причина: {reason}")

    return 0


if __name__ == "__main__":
    sys.exit(main())