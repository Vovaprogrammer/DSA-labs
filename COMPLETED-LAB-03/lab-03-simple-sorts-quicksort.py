#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки и QuickSort с рандомизацией — стартовая заготовка.

Заготовка — это каркас, а не решение: заполните все TODO самостоятельно
в соответствии с КИМ-03 и правилами использования генеративного ИИ
(docs/ai-verification.md).

Запуск: python lab03-simple-sorts-quicksort-starter.py --variant N
"""
from __future__ import annotations
from dataclasses import dataclass, field

import argparse
import random
import statistics
import time
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")          # рисуем сразу в файл, окно не нужно
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Простые сортировки со счётчиками (сортируют КОПИЮ входа, вход не меняют)
#    Каждая функция возвращает кортеж: (отсортированный список,
#    число сравнений ключей, число обменов/перемещений элементов).
# ---------------------------------------------------------------------------


def bubble_sort(a: list) -> tuple[list, int, int]:
    """Сортировка пузырьком. Ожидаемая сложность: Θ(n²). В лучшем случае: Θ(n)."""
    comp = 0
    exch = 0
    a = a.copy()
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            comp += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                exch += 1
                swapped = True
        if not swapped:
            break
    return a, comp, exch


def insertion_sort(a: list) -> tuple[list, int, int]:
    """Сортировка вставками. Ожидаемая сложность: Θ(n²). В лучшем случае: Θ(n)."""
    comp = 0
    shft = 0
    a = a.copy()
    n = len(a)
    for i in range(1, n):
        x = a[i]
        j = i - 1
        while j >= 0:
            comp += 1
            if a[j] > x:
                a[j + 1] = a[j]
                shft += 1
                j -= 1
            else:
                break
        a[j + 1] = x
    return a, comp, shft


def selection_sort(a: list) -> tuple[list, int, int]:
    """Сортировка выбором. Ожидаемая сложность: Θ(n²) — в любом случае."""
    comp = 0
    exch = 0
    a = a.copy()
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            comp += 1
            if a[m] > a[j]:
                m = j
        if i != m:
            a[i], a[m] = a[m], a[i]
            exch += 1
    return a, comp, exch


# ---------------------------------------------------------------------------
# 2. QuickSort с рандомизированным опорным элементом
# ---------------------------------------------------------------------------


def quick_sort(a: list, rng: random.Random | None = None) -> list:
    """QuickSort с выбором опорного через rng.randrange.
    Ожидаемая сложность: в среднем Θ(n log n), в худшем случае Θ(n²)."""
    if rng is None:
        rng = random.Random()
    b = a.copy()

    def partition(lo, hi):
        p = b[hi]  # опорный
        i = lo     # граница: левее i — элементы < p
        for j in range(lo, hi):
            if b[j] < p:
                b[i], b[j] = b[j], b[i]
                i += 1
        b[i], b[hi] = b[hi], b[i]
        return i   # итоговое место опорного

    def sort(lo, hi):
        if lo >= hi:  # 0 или 1 элемент
            return
        k = rng.randrange(lo, hi + 1)
        b[k], b[hi] = b[hi], b[k]
        m = partition(lo, hi)
        sort(lo, m - 1)
        sort(m + 1, hi)

    sort(0, len(b) - 1)
    return b


# ---------------------------------------------------------------------------
# 3. Демонстрация стабильности на парах (ключ, метка)
# ---------------------------------------------------------------------------


@dataclass(order=True)
class Pair:
    key: int
    label: str = field(compare=False)   # метка в сравнении не участвует


def stability_demo() -> None:
    src = [Pair(2, "a"), Pair(1, "b"), Pair(2, "c"), Pair(1, "d")]
    algos = {
        "bubble_sort": lambda a: bubble_sort(a)[0],
        "insertion_sort": lambda a: insertion_sort(a)[0],
        "selection_sort": lambda a: selection_sort(a)[0],
        "quick_sort": lambda a: quick_sort(a, random.Random(0)),
    }
    print("\nСтабильность (порядок меток при равных ключах)")
    print("вход:", [(p.key, p.label) for p in src])
    for name, fn in algos.items():
        res = fn(src)
        # метки с ключом 1 и 2 в исходном порядке: b,d и a,c
        stable = ([p.label for p in res if p.key == 1] == ["b", "d"]
                  and [p.label for p in res if p.key == 2] == ["a", "c"])
        print(f"  {name:<15}", [(p.key, p.label) for p in res],
              "-> стабильна" if stable else "-> НЕстабильна")


# ---------------------------------------------------------------------------
# 4. Классы входов (данные по варианту, детерминированно по seed)
# ---------------------------------------------------------------------------


def make_inputs(n: int, seed: int) -> dict[str, list[int]]:
    """Три класса входов размера n: упорядоченный, случайный, обратный."""
    rng = random.Random(seed + n)  # свой поток для каждого размера
    data = [rng.randint(-1_000_000, 1_000_000) for _ in range(n)]
    return {
        "упорядоченный": sorted(data),
        "случайный": data,
        "обратный": sorted(data, reverse=True),
    }


# ---------------------------------------------------------------------------
# 5. Верификация (шаги 1–3 методики docs/ai-verification.md)
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "bubble_sort": lambda a: bubble_sort(a)[0],
    "insertion_sort": lambda a: insertion_sort(a)[0],
    "selection_sort": lambda a: selection_sort(a)[0],
    "quick_sort": lambda a: quick_sort(a, random.Random(0)),
}


def is_sorted(a: list) -> bool:
    """Инвариант 1: неубывающий порядок элементов."""
    return all(a[i] <= a[i + 1] for i in range(len(a) - 1))


def self_check() -> None:
    """Граничные случаи, инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],                    # пустой массив
        [7],                   # один элемент
        [5, 5, 5, 5],          # все элементы равны
        [1, 2, 3, 4, 5],       # уже отсортирован
        [5, 4, 3, 2, 1],       # обратный порядок
    ]
    for name, fn in ALGORITHMS.items():
        for a in boundary:
            res = fn(list(a))
            assert is_sorted(res), f"{name}: нарушен порядок на {a}"
            assert sorted(res) == sorted(a), f"{name}: не перестановка входа {a}"

    # Сверка с эталоном из стандартной библиотеки на сотнях случайных входов.
    rng = random.Random(0)
    for _ in range(300):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        expected = sorted(a)
        for name, fn in ALGORITHMS.items():
            assert fn(list(a)) == expected, f"{name}: расходится с sorted() на {a}"

    # Счётчики: у сортировки выбором ровно n*(n-1)/2 сравнений на любом входе.
    _, comparisons, _ = selection_sort([3, 1, 2, 5, 4])
    assert comparisons == 10, "selection_sort: неверный счётчик сравнений"
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 6. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]     # для простых сортировок
SIZES_QUICK = [1_000, 3_000, 10_000, 30_000, 100_000]   # для QuickSort
REPEATS = 5


def bench(fn, data: list) -> float:
    """Медиана времени выполнения fn(копия data) по REPEATS запускам, с прогревом."""
    fn(list(data))  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        arg = list(data)  # свежая копия: сортировка не должна получать свой результат
        t0 = time.perf_counter()
        fn(arg)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


CLASSES = ["упорядоченный", "случайный", "обратный"]


def run_benchmarks(seed: int) -> dict:
    """Замеры всех алгоритмов на трёх классах входов.
    Возвращает {алгоритм: {класс входа: [(n, время), ...]}}."""
    plans = [
        ("bubble_sort", ALGORITHMS["bubble_sort"], SIZES_QUADRATIC),
        ("insertion_sort", ALGORITHMS["insertion_sort"], SIZES_QUADRATIC),
        ("selection_sort", ALGORITHMS["selection_sort"], SIZES_QUADRATIC),
        ("quick_sort", lambda a: quick_sort(a, random.Random(seed)), SIZES_QUICK),
    ]
    results = {name: {cls: [] for cls in CLASSES} for name, _, _ in plans}
    for name, fn, sizes in plans:
        print(f"\n{name}:")
        for n in sizes:
            for cls, data in make_inputs(n, seed).items():
                t = bench(fn, data)
                results[name][cls].append((n, t))
                print(f"  n={n:>7}  вход={cls:<13} t={t:.6f} c")
    return results


def run_counters(seed: int) -> dict:
    """Счётчики простых сортировок: {алгоритм: {класс: [(n, сравнения, обмены), ...]}}."""
    funcs = {"bubble_sort": bubble_sort, "insertion_sort": insertion_sort,
             "selection_sort": selection_sort}
    counters = {name: {cls: [] for cls in CLASSES} for name in funcs}
    for name, fn in funcs.items():
        for n in SIZES_QUADRATIC:
            for cls, data in make_inputs(n, seed).items():
                _, comp, moves = fn(data)
                counters[name][cls].append((n, comp, moves))
    return counters


def slope(points: list) -> float:
    """Наклон прямой в log-log осях (МНК): t ~ n^slope."""
    xs = np.log([n for n, _ in points])
    ys = np.log([t for _, t in points])
    return float(np.polyfit(xs, ys, 1)[0])


def print_slopes(results: dict) -> None:
    print("\nНаклоны в log-log осях (МНК по всем точкам):")
    print("| Алгоритм | " + " | ".join(CLASSES) + " |")
    print("| --- | " + " | ".join("---" for _ in CLASSES) + " |")
    for name, by_cls in results.items():
        cells = " | ".join(f"{slope(by_cls[cls]):.2f}" for cls in CLASSES)
        print(f"| {name} | {cells} |")


def print_counter_tables(counters: dict) -> None:
    for name, by_cls in counters.items():
        print(f"\nСчётчики {name} (сравнения / обмены):")
        print("| n | " + " | ".join(CLASSES) + " |")
        print("| --- | " + " | ".join("---" for _ in CLASSES) + " |")
        for i, (n, _, _) in enumerate(by_cls[CLASSES[0]]):
            cells = " | ".join(f"{by_cls[cls][i][1]} / {by_cls[cls][i][2]}" for cls in CLASSES)
            print(f"| {n} | {cells} |")


def plot_results(results: dict, variant: int) -> None:
    """Три графика (по классу входа), все алгоритмы, оси log-log."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    for ax, cls in zip(axes, CLASSES):
        for name, by_cls in results.items():
            ns, ts = zip(*by_cls[cls])
            ax.plot(ns, ts, marker="o", label=name)
        # опорные линии: n² через первую точку selection_sort, n log n — quick_sort
        n0, t0 = results["selection_sort"][cls][0]
        nq0, tq0 = results["quick_sort"][cls][0]
        ns_sq = [n for n, _ in results["selection_sort"][cls]]
        ns_q = [n for n, _ in results["quick_sort"][cls]]
        ax.plot(ns_sq, [t0 * (n / n0) ** 2 for n in ns_sq], "k--", alpha=0.4, label="~ n²")
        ax.plot(ns_q, [tq0 * (n * np.log(n)) / (nq0 * np.log(nq0)) for n in ns_q],
                "k:", alpha=0.6, label="~ n log n")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"Вход: {cls}")
        ax.set_xlabel("n")
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("время, с")
    axes[0].legend()
    fig.suptitle(f"Время сортировки от размера входа (вариант {variant}, log-log)")
    fig.tight_layout()
    fname = f"lab03_variant{variant}_loglog.png"
    fig.savefig(fname, dpi=150)
    print(f"\nГрафик сохранён: {fname}")


def save_json(results: dict, counters: dict, variant: int) -> None:
    fname = f"lab03_variant{variant}_results.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump({"variant": variant, "time": results, "counters": counters},
                  f, ensure_ascii=False, indent=1)
    print(f"Результаты сохранены: {fname}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    self_check()
    stability_demo()
    results = run_benchmarks(seed)
    counters = run_counters(seed)
    print_slopes(results)
    print_counter_tables(counters)
    plot_results(results, args.variant)
    save_json(results, counters, args.variant)


if __name__ == "__main__":
    main()
