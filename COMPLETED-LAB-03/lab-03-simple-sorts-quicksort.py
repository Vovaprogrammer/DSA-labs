#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки и QuickSort с рандомизацией опорного элемента.

Реализовано: сортировки пузырьком, вставками и выбором со счётчиками операций;
QuickSort со случайным опорным элементом и трёхсторонним разбиением;
демонстрация стабильности; самопроверка (инварианты, сверка с sorted(),
счётчики); бенчмарк с log-log графиком и таблицами счётчиков.

Запуск: python lab-03-simple-sorts-quicksort.py --variant N
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import numpy as np

plt.switch_backend("Agg")  # рисуем сразу в файл, окно не нужно

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
    """QuickSort с выбором опорного через rng.randrange и трёхсторонним разбиением.
    Ожидаемая сложность: в среднем Θ(n log n), в худшем случае Θ(n²)."""
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
# 3. Демонстрация стабильности на парах (ключ, метка)
# ---------------------------------------------------------------------------


@dataclass(order=True)
class Pair:
    """Пара (ключ, метка); сравнивается только по ключу."""

    key: int
    label: str = field(compare=False)  # метка в сравнении не участвует


def stability_demo() -> None:
    """Показать, какие из четырёх сортировок стабильны."""
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
        # метки с ключом 1 и 2 должны остаться в исходном порядке: b,d и a,c
        ok1 = [p.label for p in res if p.key == 1] == ["b", "d"]
        ok2 = [p.label for p in res if p.key == 2] == ["a", "c"]
        verdict = "стабильна" if ok1 and ok2 else "НЕстабильна"
        print(f"  {name:<15}", [(p.key, p.label) for p in res], "->", verdict)


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


def count_inversions(a: list) -> int:
    """Эталон: число инверсий полным перебором пар, O(n²)."""
    return sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j])


def self_check() -> None:
    """Граничные случаи, инварианты, сверка с sorted() и проверка счётчиков."""
    boundary = [
        [],
        [7],
        [2, 1],
        [1, 2],  # пустой, один, два элемента
        [5, 5, 5, 5],  # все элементы равны
        [1, 2, 3, 4, 5],  # уже отсортирован
        [5, 4, 3, 2, 1],  # обратный порядок
        [3, -1, 0, -1, 3],
        [-5, -2, -9],  # отрицательные числа и дубликаты
    ]
    for name, fn in ALGORITHMS.items():
        for a in boundary:
            orig = list(a)
            res = fn(a)
            assert is_sorted(res), f"{name}: нарушен порядок на {a}"
            assert Counter(res) == Counter(orig), f"{name}: не перестановка входа {a}"
            assert a == orig, f"{name}: изменил входной список {orig}"

    # Сверка с эталоном sorted() на сотнях случайных входов (с дубликатами).
    rng = random.Random(0)
    for _ in range(500):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        expected = sorted(a)
        for name, fn in ALGORITHMS.items():
            assert fn(list(a)) == expected, f"{name}: расходится с sorted() на {a}"

    # Счётчики операций: сверка с теорией.
    for _ in range(300):
        a = [rng.randint(-20, 20) for _ in range(rng.randint(0, 60))]
        n, inv = len(a), count_inversions(a)
        _, bc, be = bubble_sort(a)
        _, ic, ish = insertion_sort(a)
        _, sc, se = selection_sort(a)
        assert be == inv and ish == inv, f"обмены/сдвиги != числу инверсий на {a}"
        assert sc == n * (n - 1) // 2, f"selection: сравнений != n(n-1)/2 на {a}"
        assert se <= max(n - 1, 0), f"selection: обменов больше n-1 на {a}"
        assert bc <= n * (n - 1) // 2, f"bubble: сравнений больше n(n-1)/2 на {a}"
        if n >= 1:
            assert (
                n - 1 <= ic <= n * (n - 1) // 2
            ), f"insertion: сравнения вне границ на {a}"

    # Лучший и худший случаи: точные значения счётчиков.
    for n in (1, 2, 10, 100):
        up, down = list(range(n)), list(range(n, 0, -1))
        assert bubble_sort(up)[1:] == (n - 1, 0) and insertion_sort(up)[1:] == (
            n - 1,
            0,
        )
        assert bubble_sort(down)[1:] == (n * (n - 1) // 2,) * 2
        assert insertion_sort(down)[2] == n * (n - 1) // 2

    # QuickSort на большом входе.
    big = [rng.randint(-(10**6), 10**6) for _ in range(20000)]
    assert quick_sort(big, random.Random(1)) == sorted(
        big
    ), "quick_sort: сбой на 20000 элементах"

    # Вырожденный вход: много одинаковых элементов.
    same = [5] * 2000
    assert (
        quick_sort(same, random.Random(1)) == same
    ), "quick_sort: сбой на равных элементах"
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 6. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]  # для простых сортировок
SIZES_QUICK = [1_000, 3_000, 10_000, 30_000, 100_000]  # для QuickSort
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
    """Счётчики простых сортировок: {алгоритм: {класс: [(n, сравн., обмены)]}}."""
    funcs = {
        "bubble_sort": bubble_sort,
        "insertion_sort": insertion_sort,
        "selection_sort": selection_sort,
    }
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
    """Таблица наклонов log-log графиков (формат Markdown)."""
    print("\nНаклоны в log-log осях (МНК по всем точкам):")
    print("| Алгоритм | " + " | ".join(CLASSES) + " |")
    print("| --- | " + " | ".join("---" for _ in CLASSES) + " |")
    for name, by_cls in results.items():
        cells = " | ".join(f"{slope(by_cls[cls]):.2f}" for cls in CLASSES)
        print(f"| {name} | {cells} |")


def print_counter_tables(counters: dict) -> None:
    """Таблицы счётчиков сравнений и обменов (формат Markdown)."""
    for name, by_cls in counters.items():
        print(f"\nСчётчики {name} (сравнения / обмены):")
        print("| n | " + " | ".join(CLASSES) + " |")
        print("| --- | " + " | ".join("---" for _ in CLASSES) + " |")
        for i, (n, _, _) in enumerate(by_cls[CLASSES[0]]):
            cells = " | ".join(
                f"{by_cls[cls][i][1]} / {by_cls[cls][i][2]}" for cls in CLASSES
            )
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
        ax.plot(
            ns_sq, [t0 * (n / n0) ** 2 for n in ns_sq], "k--", alpha=0.4, label="~ n²"
        )
        ax.plot(
            ns_q,
            [tq0 * (n * np.log(n)) / (nq0 * np.log(nq0)) for n in ns_q],
            "k:",
            alpha=0.6,
            label="~ n log n",
        )
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
    """Сохранить результаты замеров и счётчики в JSON."""
    fname = f"lab03_variant{variant}_results.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(
            {"variant": variant, "time": results, "counters": counters},
            f,
            ensure_ascii=False,
            indent=1,
        )
    print(f"Результаты сохранены: {fname}")


def main() -> None:
    """Самопроверка, демонстрация стабильности, замеры, графики."""
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
