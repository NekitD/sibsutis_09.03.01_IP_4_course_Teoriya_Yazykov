import sys
from collections import deque

class Automaton:
    
    def __init__(self, alphabet, all_states, trans_table, init_state, final_q):
        self.alphabet = list(alphabet)
        self.all_states = list(all_states)
        self.trans_table = {}
        for key, val in trans_table.items():
            self.trans_table[key] = set(val) #(q0, 1): [q0, q1]
        self.init_state = init_state
        self.final_q = set(final_q)
        
        
    def print_init(self, header="Автомат"):
        print(f"\n{header}")
        print("Алфавит:", "{" + ", ".join(self.alphabet) + "}")
        print("Список состояний:", "{" + ", ".join(map(str, self.all_states)) + "}")
        print("Начальное состояние(q0):", self.init_state)
        finals_str = ", ".join(sorted(map(str, self.final_q))) or "—"
        print("Конечные состояния(qf): ", "{" + finals_str + "}")
        print("Список переходов:")
        for st in self.all_states:
            for sym in self.alphabet:
                tg = sorted(map(str, self.moves(st, sym)))
                if tg:
                    print(f"  {st} -{sym}-> {{{', '.join(tg)}}}")
                else:
                    print(f"  {st} -{sym}-> -")
        
    def moves(self, st, sym):
        return self.trans_table.get((st, sym), set()) #переходы откуда по символу
    

def read_lines(fname):
    with open(fname, encoding="utf-8") as fh:
        return [row.strip() for row in fh if row.strip()]

def loading_from_file(fname):
    
    lines = read_lines(fname)
    
    if len(lines) < 4:
        raise ValueError("Некорректный формат входных данных!")
    
    alphabet = lines[0].split()
    all_states = lines[1].split()
    init_state = lines[2]
    final_row = lines[3]
    final_q = [] if final_row == "-" else final_row.split()
    
    if not alphabet:
        raise ValueError("Алфавит пустой!")
    if not all_states:
        raise ValueError("Список состояний пустой!")
    if init_state not in all_states:
        raise ValueError(f"Начальное состояние {init_state!r} неизвестно!")
    for st in final_q:
        if st not in all_states:
            raise ValueError(f"Финальное состояние {st!r} неизвестно!")
    
    trans_table = {}
    step_no = 0
    for row in lines[4:]:
        step_no += 1
        tokens = row.split()
        if len(tokens) != 3:
            raise ValueError( f"Переход #{step_no}: нужно 'из символ в', получено {row!r}")
        src, sym, dst = tokens

        if src not in all_states or dst not in all_states:
            raise ValueError(f"Переход #{step_no} - неизвестное состояние")
        if sym not in alphabet:
            raise ValueError(f"Переход #{step_no}: символ {sym!r} не из алфавита")

        trans_table.setdefault((src, sym), set()).add(dst)

    return Automaton(alphabet, all_states, trans_table, init_state, final_q)

def is_dka(Aut):
    r = []
    for (st, sym), targets in Aut.trans_table.items(): #проходимся по (("q0","0"), {"q1"}) - True, (("q0","0"), {"q1","q2"}) - False => недетерминированный
        if len(targets) > 1:
            r.append( f"{st} -{sym}-> {{{', '.join(sorted(map(str, targets)))}}} " 
                           f"(возможных переходов {len(targets)}, ожидалось ≤ 1)")
    return (len(r) == 0, r)

def build_kda(nda):

    start_set = frozenset([nda.init_state])
    pending = deque([start_set]) #очередь не обработанных множеств
    known_sets = {start_set} #все множества, которые уже видели
    edges = {} #словарь будущих переходов
    
    name_of = {start_set: "S0"}
    next_id = 1

    while pending: #идем по множествам
        
        cur_set = pending.popleft() #первое множество из очереди
        cur_name = name_of[cur_set]

        for sym in nda.alphabet: #для каждого символа ищем куда пойти
            nxt = set() #объединение всех состояний множества
            for st in cur_set:
                nxt |= nda.moves(st, sym)

            if not nxt:
                continue

            nxt_set = frozenset(nxt)

            # Если такое множество ещё не встречалось — регистрируем его:
            # добавляем в known_sets, даём имя, ставим в очередь.
            if nxt_set not in known_sets:
                known_sets.add(nxt_set)
                name_of[nxt_set] = f"S{next_id}"
                next_id += 1
                pending.append(nxt_set)

            edges[(cur_name, sym)] = {name_of[nxt_set]} # ("S0", "0"): {"S1"}

    dka_states = []
    for s in sorted(known_sets, key=lambda x: name_of[x]): #сортируем
        dka_states.append(name_of[s])

    #находим хотябы одно финальное состояние
    dka_finals = []
    for s_set in known_sets:
        for st in s_set:
            if st in nda.final_q:
                dka_finals.append(name_of[s_set])
                break

    dka_init = name_of[start_set]

    dka = Automaton(nda.alphabet, dka_states, edges, dka_init, dka_finals)

    correspondence = {name_of[s]: s for s in known_sets}
    return dka, correspondence


def make_complete(Aut):

    holes = []
    for st in Aut.all_states:
        for sym in Aut.alphabet:
            if not Aut.moves(st, sym): #ищем пары без перехода
                holes.append((st, sym))

    if not holes:
        return Aut, None #Автомат полный

    trap = "TRAP"
    while trap in Aut.all_states:
        trap += "_"

    new_table = {}
    for key, val in Aut.trans_table.items(): #key — пара (st, sym); val — множество целей (set)
        new_table[key] = set(val)


    for st, sym in holes:
        new_table[(st, sym)] = {trap}

    # внутри ловушки по всем символам снова в ловушку
    for sym in Aut.alphabet:
        new_table[(trap, sym)] = {trap}


    new_states = list(Aut.all_states) + [trap]

    new_Aut = Automaton(
        Aut.alphabet,
        new_states,
        new_table,
        Aut.init_state,
        Aut.final_q,
    )
    return new_Aut, trap


def remove_unreachable(aut):

    reached = {aut.init_state}
    queue = deque([aut.init_state])

    while queue:
        cur = queue.popleft()
        for sym in aut.alphabet:
            for tg in aut.moves(cur, sym): # Если этого состояния ещё не встречали — новое.
                if tg not in reached:
                    reached.add(tg)
                    queue.append(tg)

    removed = [st for st in aut.all_states if st not in reached]

    if removed:
        print("Удалены:", ", ".join(map(str, removed)))
    else:
        print("Все состояния достижимы.")


    new_states = [st for st in aut.all_states if st in reached]

    # Оставляем только переходы ИЗ достижимых состояний.
    new_table = {
        key: set(val)
        for key, val in aut.trans_table.items()
        if key[0] in reached
    }

    new_finals = [st for st in aut.final_q if st in reached]

    new_aut = Automaton(
        aut.alphabet,
        new_states,
        new_table,
        aut.init_state,
        new_finals,
    )

    new_aut.print_init("ДКА после удаления недостижимых")

    return new_aut


def print_round(parts, r_num):
    line = " | ".join(
        "{" + ", ".join(sorted(map(str, grp))) + "}"
        for grp in parts
    )
    print(f"  R({r_num}) = {line}")

def build_classes(auto):

    accepting = set(auto.final_q)
    rejecting = set(auto.all_states) - accepting
    blocks = []
    if rejecting:
        blocks.append(rejecting)
    if accepting:
        blocks.append(accepting)

    r_num = 0

    print_round(blocks, r_num)

    while True:
        block_id = {}
        for num, group in enumerate(blocks):
            for state in group:
                block_id[state] = num


        refined = []
        for group in blocks:
            buckets = {}
            for state in group:
                key = tuple(
                    block_id[next(iter(auto.moves(state, letter)))]
                    for letter in auto.alphabet
                )
                buckets.setdefault(key, set()).add(state)
            refined.extend(buckets.values())

        r_num += 1
        print_round(refined, r_num)

        if len(refined) == len(blocks):
            print(f"Финальное разбиение R({r_num}).")
            return refined
        blocks = refined


def minimization(auto, partition):

    block_id = {}
    for num, group in enumerate(partition):
        for state in group:
            block_id[state] = num

    start_block = block_id[auto.init_state]
    order = []
    seen = {start_block}
    queue = deque([start_block])
    while queue:
        num = queue.popleft()
        order.append(num)

        sample = sorted(partition[num], key=str)[0]

        for letter in auto.alphabet:
            next_state = next(iter(auto.moves(sample, letter)))
            next_block = block_id[next_state]
            if next_block not in seen:
                seen.add(next_block)
                queue.append(next_block)

    names = {num: f"s{i}" for i, num in enumerate(order)}

    new_trans = {}
    for num in order:
        sample = sorted(partition[num], key=str)[0]
        for letter in auto.alphabet:
            next_state = next(iter(auto.moves(sample, letter)))
            next_block = block_id[next_state]
            new_trans[(names[num], letter)] = {names[next_block]}

    new_finals = [
        names[num] for num in order
        if partition[num].intersection(auto.final_q)
    ]

    new_auto = Automaton(
        auto.alphabet,
        list(names.values()),
        new_trans,
        names[start_block],
        new_finals,
    )

    print("Соответствие классов новым состояниям:")
    for num in order:
        old_set = sorted(map(str, partition[num]))
        print(f"{names[num]} = {{{', '.join(old_set)}}}")

    return new_auto


def drop_trap(auto, trap_name):
    new_states = [st for st in auto.all_states if st != trap_name]

    new_trans = {}
    for (src, sym), targets in auto.trans_table.items():
        if src == trap_name:
            continue
        filtered = {t for t in targets if t != trap_name}
        if filtered:
            new_trans[(src, sym)] = filtered

    return Automaton(
        auto.alphabet,
        new_states,
        new_trans,
        auto.init_state,
        auto.final_q,
    )



if __name__ == "__main__":
    try:
        machine = loading_from_file("file.txt")
    except (OSError, ValueError) as err:
        sys.exit(f"Ошибка чтения файла!: {err}")

    machine.print_init("Входной автомат")



    ok, reasons = is_dka(machine)
    if ok:
        print("\nАвтомат уже детерминированный.")
        dka = machine
    else:
        print("\nАвтомат недетерминированный.")
        for r in reasons:
            print("-", r)
        dka, corr = build_kda(machine)
        print("\nСоответствие новых состояний старым множествам:")
        for name in dka.all_states:
            old_set = sorted(map(str, corr[name]))
            print(f"  {name} = {{{', '.join(old_set)}}}")
        dka.print_init("ДКА после детерминизации")



    work, trap = make_complete(dka)
    if trap is None:
        print("  Автомат уже полный.")
    else:
        print(f"  Добавлена ловушка {trap!r}.")
    work.print_init("Полный ДКА")


    work = remove_unreachable(work)

    print("\nКлассы эквивалентности:")
    partition = build_classes(work)

    result = minimization(work, partition)

    if trap is not None and trap in result.all_states:
        result = drop_trap(result, trap)

    result.print_init("Минимизированный ДКА")
    