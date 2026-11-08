# Отчёт по ДЗ 2. Эксперимент: высота BST и деградация операций

**Вариант:** N = `14`
**Seed:** `30 + 14 = 44`
**Окружение:** Python `3.11`, CPU `12th Gen Intel(R) Core(TM) i5-12400F — 6 ядер.`

Код — в файле `case-02-bst-height-experiment.py`, запуск: `python COMPLETED-CASE-02/case-02-bst-height-experiment.py --variant 14`. Код отформатирован `black` и проверен `pylint`.

## 1. Высота и средняя глубина узла

### 1.1. Реализация

```python
def insert_iter(root: Node | None, key: int) -> Node:
    parent, cur = None, root
    while cur is not None:
        if key == cur.key:
            return root
        parent = cur
        cur = cur.left if key < cur.key else cur.right
    node = Node(key)
    if parent is None:
        return node
    if key < parent.key:
        parent.left = node
    else:
        parent.right = node
    return root


def tree_height(root: Node | None) -> int:
    height = -1
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node is not None:
            height = max(height, depth)
            stack.append((node.left, depth + 1))
            stack.append((node.right, depth + 1))
    return height


def avg_depth(root: Node | None) -> float:
    n = count_nodes(root)
    return sum_depths(root) / n if n else 0.0
```

`Node` — тот же, что в ЛР 5. Рекурсивная вставка ЛР 5 на упорядоченном потоке падает с `RecursionError`: глубина цепочки больше предела в 1000 кадров. Поэтому `insert_iter` спускается циклом, запоминая родителя, и подвешивает к нему новый лист (лекция 5, §4).

Обходы — со стеком пар `(узел, глубина)`: `tree_height` берёт максимум глубин, `sum_depths` — сумму, `count_nodes` считает узлы, `avg_depth` — их частное. Итеративный `inorder_keys` нужен для сверки с `sorted()` — раздел 6.

- **Время:** `insert_iter` — O(h); построение дерева — Θ(n log n) в среднем на случайном потоке, Θ(n²) на упорядоченном; обходы — Θ(n).
- **Память:** `insert_iter` — O(1), стек обхода — O(h).

### 1.2. Замеры

Случайный поток — `rng.sample(range(10 * n), n)` при `rng = random.Random(44)`, упорядоченный — `1, 2, …, n`; по одному дереву на каждое `n`. Перед замерами — `self_check: OK`.

| n | h, случайный | d, случайный | h, упорядоченный | d, упорядоченный | log₂ n |
| --- | --- | --- | --- | --- | --- |
| 100 | 12 | 6,6 | 99 | 49,5 | 6,6 |
| 300 | 18 | 9,1 | 299 | 149,5 | 8,2 |
| 1 000 | 22 | 10,6 | 999 | 499,5 | 10,0 |
| 3 000 | 22 | 12,8 | 2 999 | 1 499,5 | 11,6 |
| 10 000 | 29 | 15,7 | 9 999 | 4 999,5 | 13,3 |

h — высота в рёбрах, d — средняя глубина узла.

- **Упорядоченный поток:** ровно `h = n − 1` и `d = (n − 1)/2` — цепочка.
- **Случайный поток:** при росте `n` в 100 раз h и d выросли в 2,4 раза — порядок log₂ n (сравнение — в разделе 2). Высота одного дерева колеблется: при `n = 1000` и `3000` она одинакова.
