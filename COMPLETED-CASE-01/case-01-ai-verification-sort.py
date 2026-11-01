#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ДЗ 1. Верификация ИИ-сгенерированной сортировки — стартовая заготовка.

Заготовка — это каркас, а не решение: заполните все TODO самостоятельно
в соответствии с КИМ-01 (Cases) и методикой верификации по шагам 1–4
(docs/ai-verification.md). Проверяемый код лежит рядом, в dz01-ai-code.py;
исправлять его до завершения верификации запрещено.

Запуск: python dz01-verification-starter.py --variant N
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Загрузка проверяемого кода
# ---------------------------------------------------------------------------
# Имя файла содержит дефисы, поэтому обычный import не подходит —
# модуль загружается по пути через importlib.

AI_CODE_PATH = Path(__file__).with_name("dz01-ai-code.py")


def load_quicksort():
    """Загружает функцию quicksort из соседнего файла dz01-ai-code.py."""
    spec = importlib.util.spec_from_file_location("dz01_ai_code", AI_CODE_PATH)
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
            found.setdefault(problem.split(" (")[0], []).append(
                f"{name}, n={len(before)}"
            )
    print("Какие классы входов вскрыли нарушения:")
    for problem, cases in found.items():
        print(f"  {problem} — входов: {len(cases)}")
        for case in cases:
            print(f"    {case}")


# ---------------------------------------------------------------------------
# 3. Шаг 3 методики: сравнение с эталоном sorted()
# ---------------------------------------------------------------------------


def compare_with_reference(rng: random.Random, runs: int = 300) -> None:
    """Сверка quicksort с sorted() на сотнях случайных входов.

    Генерируйте входы разных размеров (включая маленькие: именно на них
    удобно локализовать расхождение), обязательно с дубликатами и
    отрицательными числами. Каждое расхождение печатайте вместе со входом,
    чтобы затем свести его к минимальному контрпримеру.
    """
    # TODO: цикл на runs итераций: вход -> quicksort(вход) vs sorted(вход);
    # TODO: подсчитать и напечатать число расхождений и минимальный контрпример.
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 4. Шаг 4 методики: бенчмарк на трёх классах входов
# (методика — docs/reproducibility.md: прогрев, >=5 повторов, медиана)
# ---------------------------------------------------------------------------

SIZES = [500, 1_000, 2_000, 4_000, 8_000]
REPEATS = 5
INPUT_KINDS = ("random", "sorted", "reversed")


def make_input(rng: random.Random, n: int, kind: str) -> list[int]:
    """Вход размера n одного из трёх классов: random / sorted / reversed."""
    a = [rng.randint(-1000, 1000) for _ in range(n)]
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


def run_benchmarks(seed: int) -> None:
    """Замеры quicksort на трёх классах входов; аварийные завершения фиксируются."""
    rng = random.Random(seed)
    for kind in INPUT_KINDS:
        print(f"\nкласс входа: {kind}")
        for n in SIZES:
            data = make_input(rng, n, kind)
            try:
                print(f"  n={n:>6}  t={bench(quicksort, data):.6f} c")
            except RecursionError:
                # Аварийное завершение — тоже результат верификации:
                # зафиксируйте его в отчёте вместе с размером входа.
                print(f"  n={n:>6}  RecursionError")
    # TODO: сопоставить рост времени по классам входов с заявленной в docstring
    # TODO: оценкой O(n log n); объяснить наблюдаемую деградацию и её причину в коде.


# ---------------------------------------------------------------------------
# 5. Самопроверка каркаса (граничные случаи + сверка с эталоном stdlib)
# ---------------------------------------------------------------------------


class SelfCheckError(Exception):
    """Вспомогательная функция верификации работает неверно."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def violated(original: list[int], result: list[int]) -> list[str]:
    """Какие инварианты нарушены: ["инвариант 1"], ["инвариант 2"], оба или []."""
    return [msg.split(" (")[0] for msg in check_invariants(original, result)]


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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    args = ap.parse_args()
    seed = 30 + args.variant  # вариантность — см. docs/reproducibility.md
    random.seed(seed)
    self_check()
    rng = random.Random(seed)
    run_representative_tests(rng)  # шаги 1–2
    compare_with_reference(rng, runs=300)  # шаг 3
    run_benchmarks(seed)  # шаг 4
    # TODO: по итогам шагов 1–4 сформулировать в отчёте вердикт о применимости
    # TODO: (принять / принять с доработкой / отклонить), исправить дефекты в копии
    # TODO: файла и подтвердить исправление повторной полной верификацией.


if __name__ == "__main__":
    main()
