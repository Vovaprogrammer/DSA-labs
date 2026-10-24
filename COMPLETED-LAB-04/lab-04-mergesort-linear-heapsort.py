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
import json
import random
import statistics
import sys
import time
import traceback
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.switch_backend("Agg")  # рисуем сразу в файл, окно не нужно

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
    """Просейка вниз элемента i в куче a[0:n] (max-heap), на месте.

    Сложность: O(h), h — высота поддерева узла i (не больше log₂ n).
    """
    while True:
        largest = i
        left, right = 2 * i + 1, 2 * i + 2  # потомки узла i в массиве
        if left < n and a[left] > a[largest]:
            largest = left
        if right < n and a[right] > a[largest]:
            largest = right
        if largest == i:  # узел не меньше потомков — свойство кучи выполнено
            return
        a[i], a[largest] = a[largest], a[i]
        i = largest


def build_max_heap(a: list[int]) -> None:
    """Построение max-кучи на месте: просейки от последнего внутреннего узла к корню.

    Сложность: O(n) — большинство узлов низко и просеиваются на малую высоту.
    """
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):  # узлы n//2 .. n-1 — листья, они уже кучи
        sift_down(a, i, n)


def heap_sort(a: list[int]) -> None:
    """HeapSort in-place: сортирует список a на месте, без вспомогательного массива.

    Схема: построение max-кучи просейками вниз (снизу вверх, O(n)),
    затем обмен вершины с последним элементом и просейка.
    Сложность: Θ(n log n) в среднем и худшем случае; доп. память O(1).
    """
    build_max_heap(a)
    for end in range(len(a) - 1, 0, -1):
        # максимум кучи a[0:end+1] уходит в конец, куча сокращается на 1
        a[0], a[end] = a[end], a[0]
        sift_down(a, 0, end)


def quick_sort(a: list, rng: random.Random | None = None) -> list:
    """QuickSort с выбором опорного через rng.randrange и трёхсторонним разбиением.
    Ожидаемая сложность: в среднем Θ(n log n), в худшем случае Θ(n²). (из ЛР 3)"""
    if rng is None:
        rng = random.Random()
    b = a.copy()

    def sort(lo, hi):
        if lo >= hi:  # 0 или 1 элемент
            return
        p = b[rng.randrange(lo, hi + 1)]  # опорное значение
        lt, i, gt = lo, lo, hi  # [lo, lt) < p, [lt, i) == p, (gt, hi] > p
        while i <= gt:
            if b[i] < p:
                b[lt], b[i] = b[i], b[lt]
                lt += 1
                i += 1
            elif b[i] > p:
                b[i], b[gt] = b[gt], b[i]
                gt -= 1
            else:
                i += 1
        sort(lo, lt - 1)
        sort(gt + 1, hi)

    sort(0, len(b) - 1)
    return b


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
    "quick_sort": lambda a: quick_sort(a, random.Random(0)),
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


def check_heap() -> None:
    """Свойство кучи после build_max_heap и сортировка heap_sort на месте.

    1) a[i] >= обоих потомков для каждого внутреннего узла, куча — перестановка входа;
    2) heap_sort возвращает None и сортирует тот же объект списка (in-place).
    """
    rng = random.Random(0)
    for _ in range(200):
        a = [rng.randint(0, 50) for _ in range(rng.randint(0, 100))]
        heap = list(a)
        build_max_heap(heap)
        expect(sorted(heap) == sorted(a), f"куча — не перестановка входа {a}")
        for i in range(len(heap) // 2):
            for child in (2 * i + 1, 2 * i + 2):
                expect(
                    child >= len(heap) or heap[i] >= heap[child],
                    f"свойство кучи нарушено: heap[{i}] < heap[{child}] в {heap}",
                )
        buf = list(a)
        ident = id(buf)
        expect(heap_sort(buf) is None, "heap_sort должен сортировать на месте")
        expect(id(buf) == ident and buf == sorted(a), f"heap_sort на месте: {a}")


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
    checks.append(("свойство кучи и in-place heap_sort", check_heap))
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


DISTRIBUTIONS = ["random_wide", "random_small", "sorted", "reversed", "almost_sorted"]
PLOTS_DIR = Path(__file__).resolve().parent / "plots"


def run_benchmarks(seed: int) -> dict:
    """Замеры всех шести сортировок на всех распределениях и размерах.

    Возвращает {распределение: {алгоритм: [(n, время), ...]}}.
    """
    rng = random.Random(seed)
    algorithms = [
        ("merge_sort", merge_sort),
        ("counting_sort", lambda a: counting_sort(a, key_max=max(a, default=0))),
        ("radix_sort_lsd", radix_sort_lsd),
        ("heap_sort", heap_sort),
        # свой генератор от seed: замеры QuickSort воспроизводимы
        ("quick_sort (ЛР 3)", lambda a: quick_sort(a, random.Random(seed))),
        ("sorted() (эталон)", sorted),
    ]
    results = {d: {name: [] for name, _ in algorithms} for d in DISTRIBUTIONS}
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
                t = bench(fn, data)
                results[dist_name][algo_name].append((n, t))
                print(f"    {algo_name:>18}: t = {t:.6f} c")
    return results


def slope(points: list) -> float:
    """Наклон прямой в log-log осях (МНК): t ~ n^slope."""
    xs = np.log([n for n, _ in points])
    ys = np.log([t for _, t in points])
    return float(np.polyfit(xs, ys, 1)[0])


def print_tables(results: dict) -> None:
    """Таблицы (Markdown): время при максимальном n и наклоны log-log."""
    algos = list(results[DISTRIBUTIONS[0]])
    for title, cell in (
        (f"Время при n = {SIZES[-1]}, с", lambda pts: f"{pts[-1][1]:.4f}"),
        (
            "Наклоны в log-log осях (МНК по всем точкам)",
            lambda pts: f"{slope(pts):.2f}",
        ),
    ):
        print(f"\n{title}:")
        print("| Алгоритм | " + " | ".join(DISTRIBUTIONS) + " |")
        print("| --- |" + " --- |" * len(DISTRIBUTIONS))
        for algo in algos:
            cells = [
                cell(results[d][algo]) if results[d][algo] else "—"
                for d in DISTRIBUTIONS
            ]
            print(f"| {algo} | " + " | ".join(cells) + " |")


def plot_results(results: dict, variant: int) -> None:
    """По графику на распределение, все алгоритмы, оси log-log."""
    fig, axes = plt.subplots(2, 3, figsize=(17, 9), sharex=True, sharey=True)
    # цвет закреплён за алгоритмом: на random_wide counting пропущен, и без этого
    # цвета остальных линий на этой панели сдвинулись бы
    colors = dict(
        zip(
            results[DISTRIBUTIONS[0]], plt.rcParams["axes.prop_cycle"].by_key()["color"]
        )
    )
    for ax, dist in zip(axes.flat, DISTRIBUTIONS):
        for algo, pts in results[dist].items():
            if pts:
                ns, ts = zip(*pts)
                ax.plot(ns, ts, marker="o", color=colors[algo], label=algo)
        # опорные линии через первую точку merge_sort: ~ n и ~ n log n
        n0, t0 = results[dist]["merge_sort"][0]
        ns = [n for n, _ in results[dist]["merge_sort"]]
        ax.plot(ns, [t0 * n / n0 for n in ns], "k:", alpha=0.5, label="~ n")
        ax.plot(
            ns,
            [t0 * n * np.log(n) / (n0 * np.log(n0)) for n in ns],
            "k--",
            alpha=0.5,
            label="~ n log n",
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(dist)
        ax.grid(True, which="both", alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("n")
    for ax in axes[:, 0]:
        ax.set_ylabel("время, с")
    axes.flat[-1].axis("off")
    axes.flat[-1].legend(  # легенда с панели random_small — там все шесть алгоритмов
        *axes.flat[1].get_legend_handles_labels(), loc="center", fontsize=12
    )
    fig.suptitle(f"Время сортировки от размера входа (вариант {variant}, log-log)")
    fig.tight_layout()
    PLOTS_DIR.mkdir(exist_ok=True)
    fname = PLOTS_DIR / f"lab04_variant{variant}_loglog.png"
    fig.savefig(fname, dpi=150)
    print(f"\nГрафик сохранён: {fname}")


def save_json(results: dict, variant: int) -> None:
    """Сохранить результаты замеров в JSON."""
    PLOTS_DIR.mkdir(exist_ok=True)
    fname = PLOTS_DIR / f"lab04_variant{variant}_results.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(
            {"variant": variant, "sizes": SIZES, "repeats": REPEATS, "time": results},
            f,
            ensure_ascii=False,
            indent=1,
        )
    print(f"Результаты сохранены: {fname}")


def main() -> None:
    """Самопроверка, демонстрации, эксперимент с k, бенчмарк, таблицы и график."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    self_check()
    merge_stability_demo()
    counting_range_experiment(seed)
    radix_stability_demo()
    results = run_benchmarks(seed)
    print_tables(results)
    plot_results(results, args.variant)
    save_json(results, args.variant)


if __name__ == "__main__":
    main()
