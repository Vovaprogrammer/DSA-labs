#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ДЗ 1. Верификация ИИ-сгенерированной сортировки по шагам 1–4.

Проверяемый код — dz01-ai-code.py (не изменяется), исправленная копия —
dz01-ai-code-fixed.py. Шаги: инварианты, репрезентативные тесты, сверка
с sorted(), бенчмарк на случайном, упорядоченном и обратном входах.

Запуск:
    python COMPLETED-CASE-01/case-01-ai-verification-sort.py --variant 14
    python COMPLETED-CASE-01/case-01-ai-verification-sort.py --variant 14 --fixed
"""

# имя файла с дефисами задано курсом, поэтому проверка имени модуля отключена
# pylint: disable=invalid-name

from __future__ import annotations

import argparse
import importlib.util
import json
import linecache
import math
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

plt.switch_backend("Agg")  # рисуем сразу в файл, окно не нужно

# ---------------------------------------------------------------------------
# 0. Загрузка проверяемого кода
# ---------------------------------------------------------------------------
# Имя файла содержит дефисы, поэтому обычный import не подходит —
# модуль загружается по пути через importlib.

AI_CODE_PATH = Path(__file__).with_name("dz01-ai-code.py")
FIXED_CODE_PATH = Path(__file__).with_name("dz01-ai-code-fixed.py")


def load_quicksort(path: Path = AI_CODE_PATH):
    """Загружает функцию quicksort из соседнего файла (по умолчанию — ИИ-код)."""
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.quicksort


quicksort = load_quicksort()


def call_sort(data: list[int]) -> tuple[list[int] | None, str | None]:
    """(результат, None) или (None, имя исключения): падение — тоже результат."""
    try:
        return quicksort(data), None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, type(exc).__name__


# ---------------------------------------------------------------------------
# 1. Шаг 1 методики: инварианты сортировки
# ---------------------------------------------------------------------------


def is_sorted(a: list[int]) -> bool:
    """Инвариант 1: последовательность упорядочена по неубыванию."""
    return all(a[i] <= a[i + 1] for i in range(len(a) - 1))


def same_multiset(a: list[int], b: list[int]) -> bool:
    """Инвариант 2: b — перестановка a (мультимножества элементов совпадают)."""
    return Counter(a) == Counter(b)


def check_invariants(original: list[int], result: list[int]) -> list[str]:
    """Возвращает список нарушенных инвариантов (пустой список — нарушений нет)."""
    violations = []
    if not is_sorted(result):
        i = next(i for i in range(len(result) - 1) if result[i] > result[i + 1])
        violations.append(f"инвариант 1 (упорядоченность): сбой на позиции {i}")
    if not same_multiset(original, result):
        # разность Counter оставляет только положительные остатки
        lost = (Counter(original) - Counter(result)).total()
        extra = (Counter(result) - Counter(original)).total()
        violations.append(
            f"инвариант 2 (перестановка): потеряно {lost}, лишних {extra}"
        )
    return violations


def violated(original: list[int], result: list[int]) -> list[str]:
    """Какие инварианты нарушены: ["инвариант 1"], ["инвариант 2"], оба или []."""
    return [msg.partition(" (")[0] for msg in check_invariants(original, result)]


# ---------------------------------------------------------------------------
# 2. Шаг 2 методики: репрезентативные тесты
# ---------------------------------------------------------------------------

# вдвое больше предела рекурсии: заявленному стеку O(log n) хватило бы ~11
LARGE_N = 2 * sys.getrecursionlimit()


def representative_cases(rng: random.Random) -> list[tuple[str, list[int]]]:
    """Именованные входы по классам методики (seed по варианту — через rng).

    Отсортированный и обратный входы — из различных чисел, случайный — и без
    дубликатов, и с ними: каждый класс проверяет одно свойство входа.
    """

    def distinct(n: int) -> list[int]:
        return rng.sample(range(-(10**6), 10**6), n)

    cases = [
        ("граничный: пустой", []),
        ("граничный: один элемент", [7]),
        ("граничный: два по возрастанию", [1, 2]),
        ("граничный: два по убыванию", [2, 1]),
        ("граничный: два равных", [5, 5]),
    ]
    for n in (10, LARGE_N):
        cases += [
            ("вырожденный: все равны", [3] * n),
            ("вырожденный: отсортированный", sorted(distinct(n))),
            ("вырожденный: обратный", sorted(distinct(n), reverse=True)),
        ]
    cases.append(("типовой: случайный без дубликатов", distinct(1000)))
    for n, span in ((10, 5), (100, 50), (1000, 1000)):
        data = [rng.randint(-span, span) for _ in range(n)]
        cases.append(("типовой: случайный с дубликатами", data))
    return cases


def run_representative_tests(rng: random.Random) -> None:
    """Прогоняет quicksort по классам входов: инварианты, вход не изменён, падения."""
    print("\nШаг 2. Репрезентативные тесты")
    for name, data in representative_cases(rng):
        before = list(data)
        result, error = call_sort(data)
        problems = [f"падение: {error}"] if error else check_invariants(before, result)
        if data != before:
            problems.append("вход изменён")
        print(f"  {name:<34} n={len(before):<5} {'; '.join(problems) or 'OK'}")
        if problems and result is not None and len(before) <= 10:
            print(f"  {'':<34} {before} -> {result}")


# ---------------------------------------------------------------------------
# 3. Шаг 3 методики: сравнение с эталоном sorted()
# ---------------------------------------------------------------------------


def reference_inputs(rng: random.Random, runs: int):
    """Случайные входы с отрицательными числами: 9 сочетаний размера и диапазона.

    Узкий диапазон даёт много дубликатов, широкий — почти без них.
    """
    for k in range(runs):
        max_n = (10, 100, 1000)[k % 3]
        span = (5, 100, 10**6)[k // 3 % 3]
        yield [rng.randint(-span, span) for _ in range(rng.randint(0, max_n))]


def shrink(data: list[int]) -> list[int]:
    """Удаляет элементы по одному, пока расхождение с sorted() сохраняется."""
    shrunk = True
    while shrunk:
        shrunk = False
        for i in range(len(data)):
            candidate = data[:i] + data[i + 1 :]
            if call_sort(candidate)[0] != sorted(candidate):
                data, shrunk = candidate, True
                break
    return data


def localize(data: list[int]) -> None:
    """Трассирует внешний вызов quicksort(data): выполненные строки и переменные."""
    code, lines, state = quicksort.__code__, [], {}

    def tracer(frame, event, arg):
        if event == "call":  # только самый первый вызов quicksort, без вложенных
            return tracer if frame.f_code is code and not lines else None
        if event == "line":
            lines.append(frame.f_lineno)
        elif event == "return":
            state.update(frame.f_locals)
            state["return"] = arg
        return tracer

    sys.settrace(tracer)
    try:
        quicksort(data)
    finally:
        sys.settrace(None)
    print(f"  трассировка внешнего вызова quicksort({data}):")
    for lineno in dict.fromkeys(lines):
        print(
            f"    строка {lineno}: {linecache.getline(code.co_filename, lineno).strip()}"
        )
    for name, value in state.items():
        print(f"    {name} = {value}")


def compare_with_reference(rng: random.Random, runs: int = 300) -> None:
    """Сверка quicksort с sorted(); минимальный контрпример и его трассировка."""
    print(f"\nШаг 3. Сверка с sorted() на {runs} случайных входах")
    stats = {True: [0, 0], False: [0, 0]}  # есть дубликаты -> [входов, расхождений]
    dedup, counterexamples = 0, []
    for data in reference_inputs(rng, runs):
        result, _ = call_sort(data)
        has_dups = len(set(data)) < len(data)
        stats[has_dups][0] += 1
        dedup += result == sorted(set(data))  # гипотеза «теряются ровно повторы»
        if result != sorted(data):
            stats[has_dups][1] += 1
            counterexamples.append(data)
    for has_dups, label in ((True, "с дубликатами"), (False, "без дубликатов")):
        total, bad = stats[has_dups]
        print(f"  входов {label}: {total}, расхождений: {bad}")
    print(f"  выход совпал с sorted(set(вход)) на {dedup} из {runs} входов")
    if counterexamples:
        smallest = min(counterexamples, key=len)
        minimal = shrink(smallest)
        print(f"  минимальный контрпример: {minimal} -> {call_sort(minimal)[0]}")
        print(f"  (сокращён из самого короткого расхождения {smallest})")
        localize(minimal)


# ---------------------------------------------------------------------------
# 4. Шаг 4 методики: бенчмарк на трёх классах входов
# (методика — docs/reproducibility.md: прогрев, >=5 повторов, медиана)
# ---------------------------------------------------------------------------

SIZES = [50, 100, 200, 400, 800, 1_600, 3_200, 6_400, 12_800]
REPEATS = 5
INPUT_KINDS = ("random", "sorted", "reversed")
PLOTS_DIR = Path(__file__).with_name("plots")
# цвет и маркер закреплены за классом входа; опорные линии — серые
COLORS = {"random": "#2a78d6", "sorted": "#eb6834", "reversed": "#1baf7a"}
MARKERS = {"random": "o", "sorted": "s", "reversed": "^"}
MUTED, GRID = "#52514e", "#e4e3df"


def make_input(rng: random.Random, n: int, kind: str) -> list[int]:
    """Вход размера n одного из трёх классов: random / sorted / reversed.

    Числа различные: на дубликатах ИИ-код теряет элементы, и время
    зависело бы не только от выбора опорного.
    """
    a = rng.sample(range(-(10**6), 10**6), n)
    if kind == "sorted":
        a.sort()
    elif kind == "reversed":
        a.sort(reverse=True)
    return a


def bench(fn, data: list[int]) -> float:
    """Медиана времени выполнения fn(data) по REPEATS запускам, с прогревом."""
    fn(data)  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        fn(data)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def max_depth(fn, data: list[int]) -> int:
    """Наибольшая глубина рекурсии fn(data) (при RecursionError — глубина падения)."""
    depth = deepest = 0

    def profiler(frame, event, _arg):
        nonlocal depth, deepest
        if frame.f_code is fn.__code__ and event in ("call", "return"):
            depth += 1 if event == "call" else -1
            deepest = max(deepest, depth)

    sys.setprofile(profiler)
    try:
        fn(data)
    except RecursionError:
        pass
    finally:
        sys.setprofile(None)
    return deepest


def measure(kind: str, data: list[int]) -> dict:
    """Точка бенчмарка: медиана времени и наибольшая глубина рекурсии."""
    rec = {"kind": kind, "n": len(data), "time_s": None, "error": None}
    rec["depth"] = max_depth(quicksort, data)  # отдельный запуск, не в замере
    try:
        rec["time_s"] = bench(quicksort, data)
    except RecursionError:  # аварийное завершение — тоже результат
        rec["error"] = "RecursionError"
    status = rec["error"] or f"t={rec['time_s']:.6f} c"
    print(f"  n={rec['n']:>6}  {status:<16} глубина={rec['depth']}")
    return rec


def run_benchmarks(seed: int) -> list[dict]:
    """Замеры quicksort на трёх классах входов для всех SIZES."""
    rng = random.Random(seed)
    records = []
    for kind in INPUT_KINDS:
        print(f"\nкласс входа: {kind}")
        records += [measure(kind, make_input(rng, n, kind)) for n in SIZES]
    return records


def summarize(records: list[dict]) -> dict:
    """Наклон log-log (МНК) и первый n с RecursionError по каждому классу."""
    print("\nСводка шага 4 (O(n log n) — наклон чуть больше 1, O(n²) — около 2)")
    summary = {}
    for kind in INPUT_KINDS:
        rows = [r for r in records if r["kind"] == kind]
        ok = [r for r in rows if r["error"] is None]
        k = statistics.linear_regression(
            [math.log(r["n"]) for r in ok], [math.log(r["time_s"]) for r in ok]
        ).slope
        crash = min((r["n"] for r in rows if r["error"]), default=None)
        summary[kind] = {"slope": k, "first_crash_n": crash}
        tail = f"RecursionError с n = {crash}" if crash else "без падений"
        print(f"  {kind:<9} наклон = {k:.2f}; {tail}")
    return summary


def add_guide(ax, first: dict, f, style: str, label: str) -> None:
    """Серая опорная линия c·f(n) через точку бенчмарка first."""
    c = first["time_s"] / f(first["n"])
    ax.plot(SIZES, [c * f(n) for n in SIZES], style, color=MUTED, label=label)


def plot_results(records: list[dict], title: str, path: Path) -> None:
    """Два log-log графика: время и наибольшая глубина рекурсии от n."""
    fig, (ax_t, ax_d) = plt.subplots(1, 2, figsize=(12, 5))
    for kind in INPUT_KINDS:
        rows = [r for r in records if r["kind"] == kind]
        ok = [r for r in rows if r["error"] is None]
        style = {"color": COLORS[kind], "marker": MARKERS[kind], "lw": 2}
        ax_t.plot([r["n"] for r in ok], [r["time_s"] for r in ok], label=kind, **style)
        ax_d.plot(
            [r["n"] for r in rows], [r["depth"] for r in rows], label=kind, **style
        )
    # опорные наклоны — через первую точку random (n log n) и sorted (n²)
    first = {
        kind: next(r for r in records if r["kind"] == kind) for kind in INPUT_KINDS
    }
    add_guide(ax_t, first["random"], lambda n: n * math.log2(n), ":", "∝ n log n")
    add_guide(ax_t, first["sorted"], lambda n: n * n, "--", "∝ n²")
    crash = min((r["n"] for r in records if r["error"]), default=None)
    if crash:
        ax_t.axvline(crash, color=MUTED, ls="-.", label=f"RecursionError с n = {crash}")
    ax_d.axhline(sys.getrecursionlimit(), color=MUTED, ls="--", label="предел рекурсии")
    ax_d.plot(SIZES, SIZES, ":", color=MUTED, label="n")
    for ax, name, ylabel in (
        (ax_t, "Время (медиана 5 запусков)", "время, с"),
        (ax_d, "Наибольшая глубина рекурсии", "глубина, вызовов"),
    ):
        ax.set(xscale="log", yscale="log", title=name, xlabel="n", ylabel=ylabel)
        ax.grid(True, color=GRID)
        ax.legend(frameon=False, fontsize=9)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nграфик: {path}")


def save_json(records: list[dict], summary: dict, variant: int, path: Path) -> None:
    """Сырые результаты замеров и сводка — в JSON рядом с графиком."""
    payload = {
        "target": Path(quicksort.__code__.co_filename).name,
        "variant": variant,
        "seed": 30 + variant,
        "python": sys.version.split()[0],
        "repeats": REPEATS,
        "summary": summary,
        "records": records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    print(f"результаты: {path}")


# ---------------------------------------------------------------------------
# 5. Самопроверка помощников (до проверки quicksort)
# ---------------------------------------------------------------------------


class SelfCheckError(Exception):
    """Вспомогательная функция верификации работает неверно."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def self_check() -> None:
    """Проверяет инварианты на граничных случаях и заведомо неверных выходах."""
    expect(is_sorted([]) and is_sorted([1, 2, 2, 3]), "is_sorted отверг порядок")
    expect(not is_sorted([3, 1, 2]), "is_sorted пропустил нарушение порядка")
    expect(same_multiset([2, 1, 2], [1, 2, 2]), "same_multiset отверг перестановку")
    expect(not same_multiset([1, 1, 2], [1, 2, 2]), "same_multiset: кратность")
    # каждый неверный выход должен нарушать именно свои инварианты
    for original, result, expected in (
        ([3, 1, 2], [1, 2, 3], []),
        ([3, 1, 2], [3, 1, 2], ["инвариант 1"]),
        ([3, 1, 3], [1, 3], ["инвариант 2"]),
        ([2, 1], [1, 1], ["инвариант 2"]),
        ([2, 1], [3, 0], ["инвариант 1", "инвариант 2"]),
    ):
        got = violated(original, result)
        expect(got == expected, f"{original} -> {result}: {got}, ждали {expected}")
    rng = random.Random(0)
    for _ in range(100):
        a = [rng.randint(-20, 20) for _ in range(rng.randint(0, 30))]
        expect(not check_invariants(a, sorted(a)), f"эталон отвергнут: {a}")
        # выход без дубликатов всегда упорядочен — ловит его только инвариант 2
        dups = ["инвариант 2"] if len(set(a)) < len(a) else []
        expect(violated(a, sorted(set(a))) == dups, f"потеря повторов не видна: {a}")
    print("self_check: OK")


def main() -> None:
    """Верификация по шагам 1–4: ИИ-код или (--fixed) исправленная копия."""
    global quicksort  # pylint: disable=global-statement
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    ap.add_argument("--fixed", action="store_true", help="проверить исправленную копию")
    args = ap.parse_args()
    seed = 30 + args.variant  # вариантность — см. docs/reproducibility.md
    random.seed(seed)  # от него зависит и случайный опорный исправленной копии
    if args.fixed:  # повторная верификация: те же проверки и входы, другой файл
        quicksort = load_quicksort(FIXED_CODE_PATH)
    print(f"проверяемый код: {Path(quicksort.__code__.co_filename).name}")
    self_check()
    rng = random.Random(seed)
    run_representative_tests(rng)  # шаги 1–2
    compare_with_reference(rng)  # шаг 3
    records = run_benchmarks(seed)  # шаг 4
    summary = summarize(records)
    PLOTS_DIR.mkdir(exist_ok=True)
    stem = f"case01_variant{args.variant}{'_fixed' if args.fixed else ''}"
    name = "исправленный quicksort" if args.fixed else "ИИ-quicksort"
    title = f"ДЗ 1, вариант {args.variant}: {name}"
    plot_results(records, title, PLOTS_DIR / f"{stem}_loglog.png")
    save_json(records, summary, args.variant, PLOTS_DIR / f"{stem}_results.json")


if __name__ == "__main__":
    main()
