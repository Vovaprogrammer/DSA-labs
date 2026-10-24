#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 4. MergeSort, Counting, Radix и HeapSort: оценка производительности — стартовая заготовка.

Заготовка — это каркас, а не решение: заполните все TODO самостоятельно
в соответствии с КИМ-04 и правилами использования генеративного ИИ
(docs/ai-verification.md). QuickSort перенесите из собственной ЛР 3.

Запуск: python lab04-mergesort-linear-heapsort-starter.py --variant N
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
import traceback
import tracemalloc

# ---------------------------------------------------------------------------
# 1. Сортировки (реализуются вручную; sorted() используется только как эталон)
# ---------------------------------------------------------------------------


def merge(left: list, right: list, key) -> list:
    """Стабильное слияние двух отсортированных списков в новый список.

    Стабильность: при равенстве ключей элемент из left идёт раньше.
    Сложность: Θ(len(left) + len(right)) по времени и по доп. памяти.
    """
    res = []
    i = j = 0
    while i < len(left) and j < len(right):
        # именно <=, а не <: при равных ключах первым берётся элемент из left
        if key(left[i]) <= key(right[j]):
            res.append(left[i])
            i += 1
        else:
            res.append(right[j])
            j += 1
    # одна из половин закончилась — хвост другой уже упорядочен
    res.extend(left[i:])
    res.extend(right[j:])
    return res


def merge_sort(a: list, key=lambda x: x) -> list:
    """MergeSort: возвращает новый отсортированный список, вход не меняется.

    Сложность: Θ(n log n) в любом случае; доп. память Θ(n).
    """
    if len(a) <= 1:
        return list(a)  # копия: результат не должен быть тем же объектом, что вход
    mid = len(a) // 2
    return merge(merge_sort(a[:mid], key), merge_sort(a[mid:], key), key)


def counting_sort(a: list, key_max: int, key=lambda x: x) -> list:
    """Устойчивая сортировка подсчётом: ключи — целые из диапазона [0, key_max].

    Схема: массив счётчиков -> префиксные суммы -> расстановка с конца.
    Сложность: время Θ(n + k), доп. память Θ(n + k), где k = key_max + 1.
    """
    keys = [key(x) for x in a]
    if keys and (min(keys) < 0 or max(keys) > key_max):
        # отрицательный ключ иначе молча попал бы в count[-1] — конец массива
        raise ValueError(f"ключи должны лежать в [0, {key_max}]")
    count = [0] * (key_max + 1)
    for k in keys:
        count[k] += 1
    # префиксные суммы: count[v] = число элементов с ключом <= v,
    # то есть позиция, ПОСЛЕ которой заканчивается блок ключа v
    for v in range(1, key_max + 1):
        count[v] += count[v - 1]
    res = [None] * len(a)
    # с конца: последний из равных встаёт в конец своего блока — порядок равных сохранён
    for i in range(len(a) - 1, -1, -1):
        count[keys[i]] -= 1
        res[count[keys[i]]] = a[i]
    return res


def radix_sort_lsd(a: list[int], digit_sort=counting_sort) -> list[int]:
    """RadixSort LSD по десятичным разрядам, неотрицательные целые.

    Поверх устойчивой поразрядной counting-сортировки: от младшего разряда
    к старшему. digit_sort(a, key_max, key) сортирует по одной цифре; подмена
    нужна только для демонстрации неустойчивого прохода.
    Сложность: время Θ(d·(n + 10)), доп. память Θ(n), d — число цифр максимума.
    """
    if a and min(a) < 0:
        raise ValueError("radix_sort_lsd работает только с неотрицательными целыми")
    res = list(a)
    largest = max(a, default=0)
    exp = 1
    while largest // exp > 0:
        # exp=exp фиксирует разряд текущего шага в лямбде
        res = digit_sort(res, 9, key=lambda x, exp=exp: (x // exp) % 10)
        exp *= 10
    return res


def sift_down(a: list[int], i: int, n: int) -> None:
    """Просейка вниз элемента i в куче a[0:n] (max-heap), на месте."""
    # TODO: спуск с обменом с большим из потомков, пока нарушено свойство кучи
    raise NotImplementedError


def heap_sort(a: list[int]) -> None:
    """HeapSort in-place: сортирует список a на месте, без вспомогательного массива.

    Схема: построение max-кучи просейками вниз (снизу вверх, O(n)),
    затем обмен вершины с последним элементом и просейка. Сложность: TODO.
    """
    # TODO: построение кучи + фаза извлечения максимумов
    raise NotImplementedError


def quick_sort(a: list[int]) -> list[int]:
    """QuickSort с рандомизацией опорного элемента — перенести из своей ЛР 3."""
    # TODO: скопировать собственную реализацию из ЛР 3 (КИМ-03)
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 2. Верификация: инварианты + сверка с эталоном sorted()
#    (шаги 1–3 методики docs/ai-verification.md)
# ---------------------------------------------------------------------------


class SelfCheckError(Exception):
    """Нарушен контракт или инвариант реализации."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def heap_sorted(a: list[int]) -> list[int]:
    """heap_sort сортирует на месте: проверяется тот список, который ему передали."""
    buf = list(a)
    heap_sort(buf)
    return buf


# Каждая функция возвращает отсортированный список; ключи — целые из [0, 999].
SORTS = {
    "merge_sort": lambda a: merge_sort(a),
    "counting_sort": lambda a: counting_sort(a, key_max=999),
    "radix_sort_lsd": lambda a: radix_sort_lsd(a),
    "heap_sort": lambda a: heap_sorted(a),
    "quick_sort": lambda a: quick_sort(a),
}


def check_sort(fn) -> None:
    """Граничные случаи, инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],  # пустой массив
        [7],  # один элемент
        [0],  # нулевой ключ
        [5, 5, 5],  # все элементы равны
        [1, 2, 3, 4, 5],  # уже отсортирован
        [5, 4, 3, 2, 1],  # обратный порядок
    ]
    for a in boundary:
        res = fn(list(a))
        expect(
            isinstance(res, list), f"на {a} возвращён {type(res).__name__}, а не список"
        )
        expect(res == sorted(a), f"на {a} получено {res}, ожидалось {sorted(a)}")

    # Случайные тесты: инвариант перестановки + сверка с эталоном
    rng = random.Random(0)
    for _ in range(200):
        a = [rng.randint(0, 999) for _ in range(rng.randint(0, 60))]
        res = fn(list(a))
        expect(sorted(res) == sorted(a), f"не перестановка входа {a}: получено {res}")
        expect(res == sorted(a), f"расходится с sorted() на {a}: получено {res}")


def check_stability(sort_by_key) -> None:
    """Стабильность на парах (ключ, порядковый номер); sort_by_key(pairs, key) -> list.

    Ключи из узкого диапазона [0, 5] — равных ключей много. Две независимые проверки:
    1) соседние пары: ключ растёт, либо ключ равен и номер растёт (порядок входа
       сохранён) — не опирается на эталон;
    2) совпадение с sorted(): эталон стабилен, поэтому порядок номеров обязан совпасть.
    """
    rng = random.Random(0)
    for _ in range(200):
        pairs = [(rng.randint(0, 5), i) for i in range(rng.randint(0, 100))]
        got = sort_by_key(pairs, lambda p: p[0])
        for prev, cur in zip(got, got[1:]):
            expect(
                prev[0] < cur[0] or (prev[0] == cur[0] and prev[1] < cur[1]),
                f"сортировка нестабильна: {prev} стоит перед {cur}",
            )
        expect(
            got == sorted(pairs, key=lambda p: p[0]),
            "сортировка нестабильна: при равных ключах нарушен порядок номеров",
        )


def check_digit_pass_stability() -> None:
    """Поразрядный проход radix (counting_sort по цифре) устойчив на каждом разряде.

    Целые с равной цифрой различимы, поэтому эталон — стабильный sorted() по цифре.
    """
    rng = random.Random(0)
    for _ in range(100):
        a = [rng.randint(0, 99_999) for _ in range(rng.randint(0, 100))]
        for exp in (1, 10, 100, 1_000, 10_000):

            def digit(x, exp=exp):
                return (x // exp) % 10

            expect(
                counting_sort(a, 9, key=digit) == sorted(a, key=digit),
                f"поразрядный проход неустойчив: разряд {exp}, вход {a}",
            )


def counting_sort_unstable(a: list, key_max: int, key=lambda x: x) -> list:
    """Для демонстрации: counting_sort с расстановкой с НАЧАЛА — равные переворачиваются."""
    keys = [key(x) for x in a]
    count = [0] * (key_max + 1)
    for k in keys:
        count[k] += 1
    for v in range(1, key_max + 1):
        count[v] += count[v - 1]
    res = [None] * len(a)
    for i, k in enumerate(keys):
        count[k] -= 1
        res[count[k]] = a[i]
    return res


def radix_stability_demo() -> None:
    """Проходы radix по разрядам с устойчивым и неустойчивым внутренним проходом."""
    src = [53, 31, 12, 35, 14, 52]
    print("\nRadixSort LSD: устойчивый и неустойчивый поразрядный проход")
    print("  вход:", src)
    for name, digit_sort in (
        ("устойчивый", counting_sort),
        ("неустойчивый", counting_sort_unstable),
    ):

        def traced(a, key_max, key, digit_sort=digit_sort, name=name):
            res = digit_sort(a, key_max, key=key)
            print(f"  {name:>12}, после прохода: {res}")
            return res

        res = radix_sort_lsd(src, digit_sort=traced)
        verdict = "верно" if res == sorted(src) else "НЕВЕРНО"
        print(f"  {name:>12}: итог {verdict}")


def merge_stability_demo() -> None:
    """Наглядно: порядок номеров при равных ключах после merge_sort."""
    src = [(2, 0), (1, 1), (2, 2), (0, 3), (1, 4), (2, 5), (0, 6), (1, 7)]
    res = merge_sort(src, key=lambda p: p[0])
    print("\nСтабильность merge_sort (пары (ключ, номер), сортировка только по ключу):")
    print("  вход:     ", src)
    print("  результат:", res)
    for k in sorted({key for key, _ in src}):
        nums = [num for key, num in res if key == k]
        verdict = "порядок сохранён" if nums == sorted(nums) else "порядок НАРУШЕН"
        print(f"  ключ {k}: номера {nums} -> {verdict}")


def self_check() -> None:
    """Все проверки по разделам; при любой ошибке замеры не выполняются."""
    # fn=fn фиксирует функцию текущего шага цикла (иначе все лямбды увидят последнюю)
    checks = [(name, lambda fn=fn: check_sort(fn)) for name, fn in SORTS.items()]
    checks.append(
        (
            "стабильность merge_sort",
            lambda: check_stability(lambda p, key: merge_sort(p, key=key)),
        )
    )
    checks.append(
        (
            "стабильность counting_sort",
            lambda: check_stability(lambda p, key: counting_sort(p, 5, key=key)),
        )
    )
    checks.append(("поразрядный проход radix", check_digit_pass_stability))
    failed = 0
    print("self_check:")
    for name, check in checks:
        try:
            check()
        except NotImplementedError as err:
            where = traceback.extract_tb(err.__traceback__)[-1].name
            print(f"  {name}: не реализовано — {where} (TODO)")
            failed += 1
        except SelfCheckError as err:
            print(f"  {name}: ОШИБКА — {err}")
            failed += 1
        except Exception:  # noqa: BLE001 — падение реализации тоже результат проверки
            print(f"  {name}: ИСКЛЮЧЕНИЕ")
            traceback.print_exc(file=sys.stdout)
            failed += 1
        else:
            print(f"  {name}: OK")
    # TODO: добавить собственные проверки (свойство кучи после построения,
    #       устойчивость поразрядного прохода radix) и описать их в отчёте.
    if failed:
        raise SystemExit(
            f"self_check: не пройдено разделов — {failed}; "
            f"замеры выполняются только после всех проверок."
        )
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 3. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES = [1_000, 3_000, 10_000, 30_000, 100_000]
REPEATS = 5
SMALL_KEY_MAX = 100  # узкий диапазон: counting уместен
WIDE_KEY_MAX = 10**9  # широкий диапазон: counting теряет смысл (обсудить в отчёте)


def make_datasets(rng: random.Random, n: int) -> dict[str, list[int]]:
    """Массивы разных распределений и диапазонов ключей для размера n."""
    almost = list(range(n))
    for _ in range(max(1, n // 100)):  # ~1 % случайных обменов
        i, j = rng.randrange(n), rng.randrange(n)
        almost[i], almost[j] = almost[j], almost[i]
    return {
        "random_wide": [rng.randint(0, WIDE_KEY_MAX) for _ in range(n)],
        "random_small": [rng.randint(0, SMALL_KEY_MAX) for _ in range(n)],
        "sorted": list(range(n)),
        "reversed": list(range(n, 0, -1)),
        "almost_sorted": almost,
    }


def bench(fn, data: list[int]) -> float:
    """Медиана времени fn на копии data по REPEATS запускам, с прогревом.

    Каждый запуск получает свежую копию: сортировка на месте не должна
    превращать последующие запуски в сортировку уже отсортированного массива.
    """
    fn(list(data))  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        buf = list(data)
        t0 = time.perf_counter()
        fn(buf)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


COUNTING_N = 10_000
COUNTING_KS = [10**2, 10**3, 10**4, 10**5, 10**6, 10**7]


def counting_range_experiment(seed: int) -> None:
    """counting_sort при фиксированном n и растущем k = key_max + 1: время и память."""
    rng = random.Random(seed)
    print(f"\ncounting_sort и диапазон ключей (n = {COUNTING_N}):")
    print(
        f"  {'k':>10} {'counting, c':>12} {'merge, c':>10} {'sorted(), c':>12}"
        f" {'пик памяти counting, МБ':>24}"
    )
    for k in COUNTING_KS:
        data = [rng.randrange(k) for _ in range(COUNTING_N)]
        t_cnt = bench(lambda a, k=k: counting_sort(a, key_max=k - 1), data)
        t_mrg = bench(merge_sort, data)
        t_ref = bench(sorted, data)
        tracemalloc.start()  # отдельный запуск: трассировка замедляет код
        counting_sort(data, key_max=k - 1)
        peak = tracemalloc.get_traced_memory()[1] / 2**20
        tracemalloc.stop()
        print(f"  {k:>10} {t_cnt:>12.6f} {t_mrg:>10.6f} {t_ref:>12.6f} {peak:>24.1f}")


def run_benchmarks(seed: int) -> None:
    rng = random.Random(seed)
    algorithms = [
        ("merge_sort", merge_sort),
        ("counting_sort", lambda a: counting_sort(a, key_max=max(a, default=0))),
        ("radix_sort_lsd", radix_sort_lsd),
        ("heap_sort", heap_sort),
        ("quick_sort (ЛР 3)", quick_sort),
        ("sorted() (эталон)", sorted),
    ]
    for n in SIZES:
        datasets = make_datasets(rng, n)
        print(f"\nn = {n}:")
        for dist_name, data in datasets.items():
            print(f"  распределение {dist_name}:")
            for algo_name, fn in algorithms:
                if algo_name == "counting_sort" and dist_name == "random_wide":
                    # счётчики размера ~10^9 не помещаются в память — граница
                    # применимости counting; зафиксировать в таблице свойств
                    print(f"    {algo_name:>18}: пропуск (диапазон ключей)")
                    continue
                print(f"    {algo_name:>18}: t = {bench(fn, data):.6f} c")
    # TODO: построить log-log графики (matplotlib) по каждому распределению;
    # TODO: заполнить таблицу свойств: время (лучший/средний/худший),
    #       память, стабильность, ограничения — для всех шести сортировок;
    # TODO: объяснить расхождения замеров с асимптотикой в отчёте.


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    self_check()
    merge_stability_demo()
    counting_range_experiment(seed)
    radix_stability_demo()
    run_benchmarks(seed)


if __name__ == "__main__":
    main()
