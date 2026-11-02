#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ДЗ 1. Верификация ИИ-сгенерированной сортировки.

Проверяемый код — dz01-ai-code.py (quicksort от ИИ-ассистента, не изменяется),
исправленная копия — dz01-ai-code-fixed.py. Верификация по шагам 1–4
docs/ai-verification.md: инварианты и самопроверка помощников,
репрезентативные тесты по классам входов, сверка с sorted() с сокращением
контрпримера и трассировкой строк, бенчмарк на случайном, упорядоченном и
обратном входах (время, глубина рекурсии, память) с log-log графиком и JSON.

Запуск:
    python COMPLETED-CASE-01/case-01-ai-verification-sort.py --variant 14
    python COMPLETED-CASE-01/case-01-ai-verification-sort.py --variant 14 --fixed
"""

# имя файла с дефисами задано курсом, поэтому проверка имени модуля отключена
# pylint: disable=invalid-name

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import linecache
import math
import random
import statistics
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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
    """Возвращает список нарушенных инвариантов (пустой список — нарушений нет).

    Сообщение сразу указывает место нарушения: первую пару соседей не по
    порядку или сколько и каких элементов потеряно и добавлено, — по нему
    дефект локализуется на шагах 2–3.
    """
    violations = []
    if not is_sorted(result):
        i = next(i for i in range(len(result) - 1) if result[i] > result[i + 1])
        violations.append(
            "инвариант 1 (упорядоченность): "
            f"result[{i}] = {result[i]} > result[{i + 1}] = {result[i + 1]}"
        )
    if not same_multiset(original, result):
        # разность Counter оставляет только положительные остатки
        lost = Counter(original) - Counter(result)
        extra = Counter(result) - Counter(original)
        violations.append(
            f"инвариант 2 (перестановка): потеряно {lost.total()}, "
            f"лишних {extra.total()}; например, потеряны {sorted(lost)[:5]}, "
            f"лишние {sorted(extra)[:5]}"
        )
    return violations


def violated(original: list[int], result: list[int]) -> list[str]:
    """Какие инварианты нарушены: ["инвариант 1"], ["инвариант 2"], оба или []."""
    return [msg.partition(" (")[0] for msg in check_invariants(original, result)]


# ---------------------------------------------------------------------------
# 2. Шаг 2 методики: репрезентативные тесты
# ---------------------------------------------------------------------------


# Большой размер для вырожденных классов: заявленному стеку O(log n) на нём
# хватает ~11 вызовов, а сам размер вдвое больше предела рекурсии Python.
LARGE_N = 2 * sys.getrecursionlimit()


def representative_cases(rng: random.Random) -> list[tuple[str, list[int]]]:
    """Именованные тестовые входы по классам методики.

    Обязательные классы: граничные (пустой, один, два элемента);
    вырожденные (все элементы равны, уже отсортированный, обратно
    отсортированный); типовые случайные с дубликатами и отрицательными
    числами (генерируются через rng — seed по варианту).

    Вырожденные классы — в двух размерах: 10 (выход виден целиком) и LARGE_N.
    Отсортированный и обратный входы составлены из различных чисел, а
    случайный вход есть и без дубликатов, и с ними — так каждый класс
    проверяет одно свойство входа, и дефекты не смешиваются.
    """

    def distinct(n: int) -> list[int]:
        """n различных чисел из [-10⁶, 10⁶) в случайном порядке."""
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
    """Прогоняет quicksort по всем классам входов и печатает нарушения инвариантов.

    Кроме двух инвариантов проверяется заявленное в docstring свойство
    «вход не меняется», а аварийное завершение тоже считается нарушением.
    В конце — сводка: какое нарушение какими классами входов вскрыто.
    """
    print("\nШаг 2. Репрезентативные тесты")
    found: dict[str, list[str]] = {}
    for name, data in representative_cases(rng):
        before = list(data)
        result = None
        try:
            result = quicksort(data)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            problems = [f"аварийное завершение: {type(exc).__name__}"]
        else:
            problems = check_invariants(before, result)
        if data != before:
            problems.append("вход изменён")
        print(f"  {name:<34} n={len(before):<5} {'; '.join(problems) or 'OK'}")
        if problems and result is not None and len(before) <= 10:
            print(f"  {'':<34} {before} -> {result}")
        for problem in problems:
            # ключ сводки — вид нарушения без подробностей
            found.setdefault(problem.partition(" (")[0], []).append(
                f"{name}, n={len(before)}"
            )
    print("Какие классы входов вскрыли нарушения:")
    if not found:
        print("  нарушений нет")
    for problem, cases in found.items():
        print(f"  {problem} — входов: {len(cases)}")
        for case in cases:
            print(f"    {case}")


# ---------------------------------------------------------------------------
# 3. Шаг 3 методики: сравнение с эталоном sorted()
# ---------------------------------------------------------------------------


def call_sort(data: list[int]) -> tuple[list[int] | None, str | None]:
    """(результат, None) или (None, имя исключения): падение — тоже результат."""
    try:
        return quicksort(data), None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, type(exc).__name__


def differs_from_reference(data: list[int]) -> bool:
    """Расхождение с эталоном: другой результат или аварийное завершение."""
    return call_sort(data)[0] != sorted(data)


def shrink(data: list[int]) -> list[int]:
    """Сводит контрпример к минимальному.

    Удаляет по одному элементу, пока расхождение сохраняется. Итог
    1-минимален: без любого своего элемента вход сортируется верно.
    """
    shrunk = True
    while shrunk:
        shrunk = False
        for i in range(len(data)):
            candidate = data[:i] + data[i + 1 :]
            if differs_from_reference(candidate):
                data, shrunk = candidate, True
                break
    return data


def trace_top_call(fn, data: list[int]) -> tuple[list[int], dict]:
    """Трассировка внешнего вызова fn(data) через sys.settrace.

    Возвращает номера строк, выполненных в этом вызове (без вложенных
    рекурсивных), и его локальные переменные в момент возврата;
    возвращённое значение — под ключом "return".
    """
    top, lines, state = [], [], {}

    def tracer(frame, event, arg):
        if event == "call":
            if frame.f_code is not fn.__code__ or top:
                return None  # вложенные вызовы и списковые включения не нужны
            top.append(frame)
        elif event == "line":
            lines.append(frame.f_lineno)
        elif event == "return":
            state.update(frame.f_locals)
            state["return"] = arg
        return tracer

    sys.settrace(tracer)
    try:
        fn(data)
    finally:
        sys.settrace(None)
    return list(dict.fromkeys(lines)), state


def localize(data: list[int]) -> None:
    """Печатает строки quicksort, выполненные на контрпримере, и её состояние."""
    lines, state = trace_top_call(quicksort, data)
    filename = quicksort.__code__.co_filename
    print(f"  трассировка внешнего вызова quicksort({data}):")
    for lineno in lines:
        print(f"    строка {lineno}: {linecache.getline(filename, lineno).strip()}")
    for name, value in state.items():
        print(f"    {name} = {value}")


def reference_inputs(rng: random.Random, runs: int):
    """runs случайных входов с отрицательными числами для сверки с эталоном.

    9 сочетаний размера и диапазона значений идут по очереди: узкий
    диапазон даёт много дубликатов, широкий — почти без них.
    """
    for k in range(runs):
        max_n = (10, 100, 1000)[k % 3]
        span = (5, 100, 10**6)[k // 3 % 3]
        yield [rng.randint(-span, span) for _ in range(rng.randint(0, max_n))]


def compare_with_reference(rng: random.Random, runs: int = 300) -> None:
    """Сверка quicksort с sorted() на сотнях случайных входов.

    Генерируйте входы разных размеров (включая маленькие: именно на них
    удобно локализовать расхождение), обязательно с дубликатами и
    отрицательными числами. Каждое расхождение печатайте вместе со входом,
    чтобы затем свести его к минимальному контрпримеру.

    Расхождения считаются отдельно для входов с дубликатами и без них;
    самый короткий контрпример сокращается (shrink) и трассируется
    по строкам проверяемого кода (localize).
    """
    print(f"\nШаг 3. Сверка с sorted() на {runs} случайных входах")
    inputs = {True: 0, False: 0}  # есть ли во входе дубликаты -> число входов
    mismatches = {True: 0, False: 0}
    kinds: Counter[str] = Counter()
    dedup = 0  # на скольких входах выход равен sorted(set(вход))
    counterexamples = []
    for data in reference_inputs(rng, runs):
        has_dups = len(set(data)) < len(data)
        inputs[has_dups] += 1
        result, error = call_sort(data)
        dedup += result == sorted(set(data))
        if result == sorted(data):
            continue
        mismatches[has_dups] += 1
        kinds[error or " и ".join(violated(data, result))] += 1
        counterexamples.append(data)
    for has_dups, label in ((True, "с дубликатами"), (False, "без дубликатов")):
        print(
            f"  входов {label}: {inputs[has_dups]}, "
            f"расхождений: {mismatches[has_dups]}"
        )
    for kind, count in kinds.items():
        print(f"  вид расхождения — {kind}: {count}")
    print(f"  выход совпал с sorted(set(вход)) на {dedup} из {runs} входов")
    if not counterexamples:
        print("  расхождений нет")
        return
    counterexamples.sort(key=len)
    print(f"  самые короткие расхождения (5 из {len(counterexamples)}):")
    for data in counterexamples[:5]:
        print(f"    {data} -> {call_sort(data)[0]}")
    minimal = shrink(counterexamples[0])
    print(f"  минимальный контрпример: {minimal} -> {call_sort(minimal)[0]}")
    localize(minimal)


# ---------------------------------------------------------------------------
# 4. Шаг 4 методики: бенчмарк на трёх классах входов
# (методика — docs/reproducibility.md: прогрев, >=5 повторов, медиана)
# ---------------------------------------------------------------------------

SIZES = [50, 100, 200, 400, 800, 1_600, 3_200, 6_400, 12_800]
REPEATS = 5
INPUT_KINDS = ("random", "sorted", "reversed")
# Упавшие точки до RAISED_MAX_N перемеряются с поднятым пределом рекурсии.
# Дальше не идём: на упорядоченном входе ИИ-код держит Θ(n²) памяти —
# около 170 МиБ при n = 6400 и около 670 МиБ при n = 12 800.
RAISED_LIMIT = 10_000
RAISED_MAX_N = 6_400

PLOTS_DIR = Path(__file__).with_name("plots")
# цвет закреплён за классом входа (первые три слота эталонной палитры)
COLORS = {"random": "#2a78d6", "sorted": "#eb6834", "reversed": "#1baf7a"}
MARKERS = {"random": "o", "sorted": "s", "reversed": "^"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def make_input(rng: random.Random, n: int, kind: str) -> list[int]:
    """Вход размера n одного из трёх классов: random / sorted / reversed.

    В отличие от заготовки числа различные: на дубликатах ИИ-код теряет
    элементы (раздел 4 отчёта), а глубина его рекурсии ограничена числом
    различных значений. С различными числами время зависит только от
    выбора опорного элемента.
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
    """Наибольшая глубина рекурсии fn(data) — по событиям sys.setprofile.

    При RecursionError возвращает глубину, на которой стек переполнился.
    """
    depth = deepest = 0

    def profiler(frame, event, _arg):
        nonlocal depth, deepest
        if frame.f_code is not fn.__code__:
            return  # списковые включения и встроенные функции не считаются
        if event == "call":
            depth += 1
            deepest = max(deepest, depth)
        elif event == "return":
            depth -= 1

    sys.setprofile(profiler)
    try:
        fn(data)
    except RecursionError:
        pass
    finally:
        sys.setprofile(None)
    return deepest


def peak_memory(fn, data: list[int]) -> int:
    """Пик памяти (байты), выделенной во время fn(data), — tracemalloc."""
    tracemalloc.start()
    try:
        fn(data)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@contextlib.contextmanager
def recursion_limit(limit: int):
    """Временно меняет предел рекурсии Python и затем восстанавливает его."""
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)
    try:
        yield
    finally:
        sys.setrecursionlimit(old)


def measure(kind: str, data: list[int]) -> dict:
    """Одна точка бенчмарка при текущем пределе рекурсии; печатает её."""
    rec = {
        "kind": kind,
        "n": len(data),
        "limit": sys.getrecursionlimit(),
        "time_s": None,
        "depth": max_depth(quicksort, data),
        "peak_kib": None,
        "error": None,
    }
    head = f"  n={rec['n']:>6}  предел={rec['limit']:<6}"
    try:
        rec["time_s"] = bench(quicksort, data)
    except RecursionError:
        # аварийное завершение — тоже результат верификации
        rec["error"] = "RecursionError"
        print(f"{head} RecursionError на глубине {rec['depth']}")
        return rec
    rec["peak_kib"] = peak_memory(quicksort, data) / 1024
    print(
        f"{head} t={rec['time_s']:.6f} c  глубина={rec['depth']:<5} "
        f"пик памяти={rec['peak_kib']:.0f} КиБ"
    )
    return rec


def run_benchmarks(seed: int) -> list[dict]:
    """Замеры quicksort на трёх классах входов; аварийные завершения фиксируются.

    Для каждой точки — медиана времени, наибольшая глубина рекурсии и пик
    памяти (глубина и память — в отдельных, не замеряемых по времени
    запусках). Точка, упавшая с RecursionError, при n <= RAISED_MAX_N
    перемеряется с поднятым пределом рекурсии: так видно, во что обходится
    упорядоченный вход, если стек не ограничен.
    """
    rng = random.Random(seed)
    records = []
    for kind in INPUT_KINDS:
        print(f"\nкласс входа: {kind}")
        for n in SIZES:
            data = make_input(rng, n, kind)
            records.append(measure(kind, data))
            if records[-1]["error"] and n <= RAISED_MAX_N:
                with recursion_limit(RAISED_LIMIT):
                    records.append(measure(kind, data))
    return records


def slope(points: list[tuple[int, float]]) -> float | None:
    """Наклон прямой МНК в осях log-log — показатель степени роста времени."""
    if len(points) < 2:
        return None
    xs = [math.log(n) for n, _ in points]
    ys = [math.log(t) for _, t in points]
    return statistics.linear_regression(xs, ys).slope


def summarize(records: list[dict]) -> dict:
    """Наклоны по классам входов и порог аварийного завершения; печатает сводку."""
    print("\nСводка шага 4 (для заявленной O(n log n) наклон чуть больше 1)")
    summary = {}
    for kind in INPUT_KINDS:
        rows = [r for r in records if r["kind"] == kind]
        timed = [(r["n"], r["time_s"]) for r in rows if r["time_s"] is not None]
        crashed = [r["n"] for r in rows if r["error"]]
        summary[kind] = {
            "slope": slope(timed),
            "points": len(timed),
            "first_crash_n": min(crashed, default=None),
        }
        k = summary[kind]["slope"]
        crash = f"RecursionError с n = {min(crashed)}" if crashed else "без падений"
        print(
            f"  {kind:<9} наклон = {'—' if k is None else f'{k:.2f}'} "
            f"по {len(timed)} точкам; {crash}"
        )
    return summary


def guide(ax, xs: list[int], f, anchor: tuple[int, float], label: str) -> None:
    """Опорная серая линия c·f(n) через точку anchor с подписью справа."""
    c = anchor[1] / f(anchor[0])
    ys = [c * f(x) for x in xs]
    ax.plot(xs, ys, ls=":", lw=1.2, color=MUTED, zorder=1)
    ax.annotate(
        label,
        (xs[-1], ys[-1]),
        xytext=(4, 0),
        textcoords="offset points",
        color=MUTED,
        fontsize=9,
        va="center",
    )


def style_axes(ax, title: str, ylabel: str) -> None:
    """log-log оси с приглушённой сеткой; текст — цветами текста, не серий."""
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    ax.set_xlabel("n — размер входа", color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.grid(True, which="major", color=GRID, lw=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def plot_kind(ax_t, ax_d, kind: str, rows: list[dict]) -> None:
    """Линии одного класса входа на графиках времени (ax_t) и глубины (ax_d).

    Сплошная линия — обычный предел рекурсии; пунктир с полыми маркерами —
    повторный замер упавших точек с пределом RAISED_LIMIT; крестик на
    графике глубины — глубина, на которой стек переполнился.
    """
    base = [r for r in rows if r["limit"] != RAISED_LIMIT]
    raised = [r for r in rows if r["limit"] == RAISED_LIMIT]
    ok = [r for r in base if r["error"] is None]
    crashed = [r for r in base if r["error"]]
    # у sorted и reversed почти одинаковые значения — различаем и формой маркера
    style = {"color": COLORS[kind], "marker": MARKERS[kind], "lw": 2, "ms": 6}
    ax_t.plot([r["n"] for r in ok], [r["time_s"] for r in ok], label=kind, **style)
    ax_d.plot([r["n"] for r in ok], [r["depth"] for r in ok], **style)
    if crashed:
        ax_d.plot(
            [r["n"] for r in crashed],
            [r["depth"] for r in crashed],
            ls="",
            marker="x",
            ms=8,
            mew=2,
            color=COLORS[kind],
        )
    if raised:
        tail = ok[-1:] + raised  # продолжение линии от последней удачной точки
        style.update(ls="--", mfc="white")
        ax_t.plot(
            [r["n"] for r in tail],
            [r["time_s"] for r in tail],
            label=f"{kind}, предел {RAISED_LIMIT}",
            **style,
        )
        ax_d.plot([r["n"] for r in tail], [r["depth"] for r in tail], **style)


def mark_time_axis(ax, records: list[dict], summary: dict) -> None:
    """Опорные наклоны n log n и n² и граница аварийного завершения."""
    for kind, f, label in (
        ("random", lambda n: n * math.log2(n), "∝ n log n"),
        ("sorted", lambda n: n * n, "∝ n²"),
    ):
        timed = [r for r in records if r["kind"] == kind and r["time_s"] is not None]
        if timed:
            xs = [r["n"] for r in timed]
            guide(ax, xs, f, (xs[0], timed[0]["time_s"]), label)
    crash_ns = [s["first_crash_n"] for s in summary.values() if s["first_crash_n"]]
    if crash_ns:
        ax.axvline(min(crash_ns), color=MUTED, ls="--", lw=1, zorder=1)
        ax.annotate(
            f"RecursionError при n ≥ {min(crash_ns)}\n"
            f"(предел рекурсии {sys.getrecursionlimit()})",
            (min(crash_ns), 0),
            xycoords=("data", "axes fraction"),
            xytext=(4, 6),
            textcoords="offset points",
            va="bottom",
            color=MUTED,
            fontsize=9,
        )


def mark_depth_axis(ax) -> None:
    """Предел рекурсии Python и опорные линии n и log₂ n."""
    limit = sys.getrecursionlimit()
    ax.axhline(limit, color=MUTED, ls="--", lw=1, zorder=1)
    ax.annotate(
        f"предел рекурсии Python = {limit}",
        (0, limit),
        xycoords=("axes fraction", "data"),
        xytext=(4, 4),
        textcoords="offset points",
        color=MUTED,
        fontsize=9,
    )
    guide(ax, SIZES, lambda n: n, (SIZES[0], SIZES[0]), "n")
    guide(ax, SIZES, math.log2, (SIZES[0], math.log2(SIZES[0])), "log₂ n")


def plot_results(
    records: list[dict], summary: dict, variant: int, fixed: bool = False
) -> Path:
    """Два log-log графика: время и наибольшая глубина рекурсии от n.

    fixed=True — замеры исправленной копии: другой заголовок и имя файла.
    """
    PLOTS_DIR.mkdir(exist_ok=True)
    fig, (ax_t, ax_d) = plt.subplots(1, 2, figsize=(13, 5.8))
    for kind in INPUT_KINDS:
        plot_kind(ax_t, ax_d, kind, [r for r in records if r["kind"] == kind])
    mark_time_axis(ax_t, records, summary)
    mark_depth_axis(ax_d)
    style_axes(ax_t, "Время quicksort (медиана 5 запусков)", "время, с")
    style_axes(ax_d, "Наибольшая глубина рекурсии", "глубина, вызовов")
    # одна общая легенда под графиками: серии на обоих одинаковые
    handles, labels = ax_t.get_legend_handles_labels()
    if any(r["error"] for r in records):
        handles.append(Line2D([], [], ls="", marker="x", ms=8, mew=2, color=MUTED))
        labels.append("глубина, на которой случился RecursionError")
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=9,
        labelcolor=INK,
    )
    name = "исправленный quicksort" if fixed else "ИИ-quicksort"
    fig.suptitle(
        f"ДЗ 1, вариант {variant}: {name} на случайном, упорядоченном и "
        "обратном входах",
        color=INK,
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0.09, 1, 1))  # место снизу под легенду
    suffix = "_fixed" if fixed else ""
    path = PLOTS_DIR / f"case01_variant{variant}{suffix}_loglog.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nграфик: {path}")
    return path


def save_json(
    records: list[dict], summary: dict, variant: int, fixed: bool = False
) -> Path:
    """Сырые результаты замеров и сводка — в JSON рядом с графиком."""
    PLOTS_DIR.mkdir(exist_ok=True)
    suffix = "_fixed" if fixed else ""
    path = PLOTS_DIR / f"case01_variant{variant}{suffix}_results.json"
    payload = {
        "target": (FIXED_CODE_PATH if fixed else AI_CODE_PATH).name,
        "variant": variant,
        "seed": 30 + variant,
        "python": sys.version.split()[0],
        "repeats": REPEATS,
        "sizes": SIZES,
        "raised_limit": RAISED_LIMIT,
        "summary": summary,
        "records": records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    print(f"результаты: {path}")
    return path


# ---------------------------------------------------------------------------
# 5. Самопроверка каркаса (граничные случаи + сверка с эталоном stdlib)
# ---------------------------------------------------------------------------


class SelfCheckError(Exception):
    """Вспомогательная функция верификации работает неверно."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def self_check() -> None:
    """Проверяет вспомогательные функции до основной верификации."""
    expect(
        is_sorted([]) and is_sorted([7]) and is_sorted([1, 2, 2, 3]),
        "is_sorted отверг упорядоченный вход",
    )
    expect(not is_sorted([3, 1, 2]), "is_sorted пропустил нарушение порядка")
    expect(
        same_multiset([], []) and same_multiset([2, 1, 2], [1, 2, 2]),
        "same_multiset отверг перестановку",
    )
    expect(
        not same_multiset([1, 1, 2], [1, 2, 2]),
        "same_multiset не заметил разную кратность",
    )
    # заведомо неверные выходы: каждый должен нарушать именно свои инварианты
    broken = [
        ([3, 1, 2], [1, 2, 3], []),  # верный выход
        ([3, 1, 2], [3, 1, 2], ["инвариант 1"]),  # перестановка, но не упорядочен
        ([3, 1, 3], [1, 3], ["инвариант 2"]),  # упорядочен, но потерян элемент
        ([2, 1], [1, 2, 2], ["инвариант 2"]),  # упорядочен, но лишний элемент
        ([2, 1], [1, 1], ["инвариант 2"]),  # длина та же, элемент подменён
        ([2, 1], [3, 0], ["инвариант 1", "инвариант 2"]),  # нарушены оба
    ]
    for original, result, expected in broken:
        expect(
            violated(original, result) == expected,
            f"check_invariants({original}, {result}) вернул "
            f"{violated(original, result)}, ожидалось {expected}",
        )
    rng = random.Random(0)
    for _ in range(100):  # сверка помощников с эталоном стандартной библиотеки
        a = [rng.randint(-20, 20) for _ in range(rng.randint(0, 30))]
        expect(is_sorted(sorted(a)), f"эталон sorted() не упорядочен: {a}")
        expect(not check_invariants(a, sorted(a)), f"эталон отвергнут: {a}")
        # «сортировка» без дубликатов всегда упорядочена — ловит её только инвариант 2
        has_dups = len(set(a)) < len(a)
        expect(
            violated(a, sorted(set(a))) == (["инвариант 2"] if has_dups else []),
            f"потеря дубликатов не обнаружена: {a}",
        )
        # неотсортированная копия — перестановка, ловит её только инвариант 1
        expect(
            violated(a, a) == ([] if a == sorted(a) else ["инвариант 1"]),
            f"нарушение порядка не обнаружено: {a}",
        )
    print("self_check: OK")


def main() -> None:
    """Полная верификация по шагам 1–4: ИИ-код или (--fixed) исправленная копия."""
    global quicksort  # pylint: disable=global-statement
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    ap.add_argument(
        "--fixed",
        action="store_true",
        help="проверить исправленную копию dz01-ai-code-fixed.py",
    )
    args = ap.parse_args()
    seed = 30 + args.variant  # вариантность — см. docs/reproducibility.md
    random.seed(seed)  # от него зависит и случайный опорный исправленной копии
    if args.fixed:
        # повторная верификация: те же проверки и входы, другой проверяемый файл
        quicksort = load_quicksort(FIXED_CODE_PATH)
    print(f"проверяемый код: {Path(quicksort.__code__.co_filename).name}")
    self_check()
    rng = random.Random(seed)
    run_representative_tests(rng)  # шаги 1–2
    compare_with_reference(rng, runs=300)  # шаг 3
    records = run_benchmarks(seed)  # шаг 4
    summary = summarize(records)
    plot_results(records, summary, args.variant, args.fixed)
    save_json(records, summary, args.variant, args.fixed)


if __name__ == "__main__":
    main()
