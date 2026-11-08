#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ДЗ 2. Эксперимент: высота BST и деградация операций — стартовая заготовка.

Заготовка — это каркас, а не решение: заполните все TODO самостоятельно
в соответствии с КИМ-02 (Cases) и правилами использования генеративного ИИ
(docs/ai-verification.md). Класс BST из ЛР 5 рекомендуется подключить как
модуль; ниже дан минимальный узел и сигнатуры на случай автономного запуска.

Запуск: python dz02-bst-height-starter.py --variant N
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
import time
from pathlib import Path

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Узел и итеративная вставка
#    Внимание: на упорядоченном потоке дерево вырождается в список глубиной
#    до 10^4, поэтому вставка и обходы должны быть итеративными —
#    рекурсивные варианты вызовут RecursionError.
# ---------------------------------------------------------------------------


class Node:
    """Узел BST: ключ и ссылки на левое и правое поддеревья."""

    __slots__ = ("key", "left", "right")

    def __init__(self, key: int) -> None:
        self.key = key
        self.left: Node | None = None
        self.right: Node | None = None


def insert_iter(root: Node | None, key: int) -> Node:
    """Итеративная вставка ключа в BST; возвращает корень дерева.

    Дубликаты игнорируются (ключи в эксперименте уникальны).
    """
    parent, cur = None, root
    while cur is not None:  # спуск как при неудачном поиске
        if key == cur.key:
            return root  # дубликат — дерево не меняется
        parent = cur  # запоминаем будущего родителя
        cur = cur.left if key < cur.key else cur.right
    node = Node(key)
    if parent is None:
        return node  # дерево было пустым: новый узел — корень
    if key < parent.key:
        parent.left = node
    else:
        parent.right = node
    return root


def build_bst(keys: list[int]) -> Node | None:
    """Строит BST последовательной итеративной вставкой ключей."""
    root: Node | None = None
    for key in keys:
        root = insert_iter(root, key)
    return root


# ---------------------------------------------------------------------------
# 2. Измеряемые величины: высота и средняя глубина узла
# ---------------------------------------------------------------------------


def tree_height(root: Node | None) -> int:
    """Высота дерева: число рёбер на самом длинном пути от корня до листа.

    Пустое дерево: -1; один узел: 0. Реализовать итеративно
    (обход в ширину или в глубину с явным стеком/очередью).
    """
    height = -1
    stack = [(root, 0)]  # пары (узел, его глубина)
    while stack:
        node, depth = stack.pop()
        if node is not None:
            height = max(height, depth)
            stack.append((node.left, depth + 1))
            stack.append((node.right, depth + 1))
    return height


def sum_depths(root: Node | None) -> int:
    """Сумма глубин всех узлов (глубина корня — 0). Итеративно."""
    total = 0
    stack = [(root, 0)]  # пары (узел, его глубина)
    while stack:
        node, depth = stack.pop()
        if node is not None:
            total += depth
            stack.append((node.left, depth + 1))
            stack.append((node.right, depth + 1))
    return total


def count_nodes(root: Node | None) -> int:
    """Число узлов дерева. Итеративно."""
    count = 0
    stack = [root]
    while stack:
        node = stack.pop()
        if node is not None:
            count += 1
            stack.append(node.left)
            stack.append(node.right)
    return count


def avg_depth(root: Node | None) -> float:
    """Средняя глубина узла: sum_depths / count_nodes (0.0 для пустого)."""
    n = count_nodes(root)
    return sum_depths(root) / n if n else 0.0


def inorder_keys(root: Node | None) -> list[int]:
    """Ключи in-order-обхода (итеративно, с явным стеком) — для верификации."""
    out: list[int] = []
    stack: list[Node] = []  # предки, к которым ещё предстоит вернуться
    cur = root
    while stack or cur is not None:
        while cur is not None:  # спуск влево до конца
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()  # самый левый необработанный узел
        out.append(cur.key)
        cur = cur.right  # дальше — его правое поддерево
    return out


# ---------------------------------------------------------------------------
# 3. Верификация (шаги 1–3 методики docs/ai-verification.md)
# ---------------------------------------------------------------------------


def self_check() -> None:
    """Граничные деревья, аналитические значения, сверка с эталоном sorted()."""
    # Граничные случаи: пустое дерево и один узел
    assert tree_height(None) == -1
    assert avg_depth(None) == 0.0
    single = build_bst([42])
    assert tree_height(single) == 0
    assert count_nodes(single) == 1

    # Типовой случай: [2, 1, 3] — идеально сбалансированное дерево из 3 узлов
    small = build_bst([2, 1, 3])
    assert tree_height(small) == 1
    assert sum_depths(small) == 2  # 0 (корень) + 1 + 1

    # Вырожденный случай: упорядоченные ключи 1..n дают "список"
    n = 100
    degenerate = build_bst(list(range(1, n + 1)))
    assert tree_height(degenerate) == n - 1
    assert avg_depth(degenerate) == (n - 1) / 2  # (0+1+...+(n-1)) / n

    # Сверка с эталоном стандартной библиотеки: инвариант BST —
    # in-order-обход совпадает с sorted() на случайных наборах ключей
    rng = random.Random(0)
    for _ in range(200):
        keys = rng.sample(range(-1000, 1000), rng.randint(1, 60))
        root = build_bst(keys)
        assert inorder_keys(root) == sorted(keys)
        assert count_nodes(root) == len(keys)
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 4. Эксперимент и каркас замеров (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES = [100, 300, 1_000, 3_000, 10_000]  # геометрический шаг, n до 10^4
REPEATS = 5
PLOTS_DIR = Path(__file__).with_name("plots")


def random_keys(n: int, rng: random.Random) -> list[int]:
    """n уникальных случайных ключей (детерминированно по seed варианта)."""
    return rng.sample(range(10 * n), n)


def ordered_keys(n: int) -> list[int]:
    """n упорядоченных ключей 1..n — худший поток вставок для BST."""
    return list(range(1, n + 1))


def bench_search(root: Node | None, queries: list[int]) -> float:
    """Медиана времени поиска всех ключей queries по REPEATS запускам."""

    def run() -> None:
        for q in queries:
            node = root
            while node is not None and node.key != q:
                node = node.left if q < node.key else node.right

    run()  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        run()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def plot_results(heights: tuple, depths: tuple, path: Path) -> None:
    """h(n) и d(n) для двух потоков (случайный, упорядоченный) на фоне log2(n) и n."""
    # Оси log-log: n — прямая с наклоном 1, log2(n) — почти горизонтальная кривая
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, title, (rand, ordered) in (
        (axes[0], "Высота дерева h(n)", heights),
        (axes[1], "Средняя глубина узла d(n)", depths),
    ):
        ax.plot(SIZES, rand, "o-", label="случайный поток")
        ax.plot(SIZES, ordered, "s-", label="упорядоченный поток")
        ax.plot(SIZES, [math.log2(n) for n in SIZES], ":", c="gray", label="log₂(n)")
        ax.plot(SIZES, SIZES, "--", c="gray", label="n")
        ax.set(xscale="log", yscale="log", title=title, xlabel="n")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_experiment(seed: int) -> None:
    """Таблица: n, высота и средняя глубина для двух потоков, опорные величины."""
    rng = random.Random(seed)
    header = (
        f"{'n':>7} {'h_случ':>8} {'d_случ':>8} "
        f"{'h_упор':>8} {'d_упор':>8} {'log2(n)':>8}"
    )
    print(header)
    h_rand, d_rand, h_ord, d_ord = [], [], [], []  # значения для графиков
    for n in SIZES:
        root_rand = build_bst(random_keys(n, rng))
        root_ord = build_bst(ordered_keys(n))
        h_rand.append(tree_height(root_rand))
        d_rand.append(avg_depth(root_rand))
        h_ord.append(tree_height(root_ord))
        d_ord.append(avg_depth(root_ord))
        print(
            f"{n:>7} {h_rand[-1]:>8} {d_rand[-1]:>8.1f} "
            f"{h_ord[-1]:>8} {d_ord[-1]:>8.1f} {math.log2(n):>8.1f}"
        )
        # TODO: замерить bench_search для обоих деревьев на одинаковых
        #       запросах и включить сравнение времени в отчёт
    PLOTS_DIR.mkdir(exist_ok=True)
    path = PLOTS_DIR / f"case02_variant{seed - 30}_loglog.png"
    plot_results((h_rand, h_ord), (d_rand, d_ord), path)
    print(f"график: {path}")
    # TODO: в отчёте объяснить деградацию операций до O(n), привести справку
    #       об AVL (высота <= 1.44*log2(n), цена балансировки) и
    #       вывод-рекомендацию о выборе структуры


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    self_check()
    run_experiment(seed)


if __name__ == "__main__":
    main()
