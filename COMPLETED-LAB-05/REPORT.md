# Отчёт по ЛР 5. Бинарное дерево поиска: обходы, вставка и удаление

**Вариант:** N = `14`
**Seed:** `30 + 14 = 44`
**Окружение:** Python `3.11`, CPU `12th Gen Intel(R) Core(TM) i5-12400F — 6 ядер.`

Код — в файле `lab-05-bst.py`, запуск: `python COMPLETED-LAB-05/lab-05-bst.py --variant 14`.
Код отформатирован `black` и проверен `pylint`.

## 1. Вставка, поиск и удаление

```python
def insert(self, key: int) -> None:
    def _insert(node: Node | None, key: int) -> Node:
        if node is None:
            return Node(key)
        if key < node.key:
            node.left = _insert(node.left, key)
        elif key > node.key:
            node.right = _insert(node.right, key)
        return node

    self.root = _insert(self.root, key)

def search(self, key: int) -> bool:
    cur = self.root
    while cur is not None:
        if key == cur.key:
            return True
        if key < cur.key:
            cur = cur.left
        else:
            cur = cur.right
    return False

def delete(self, key: int) -> None:
    def _delete(node: Node | None, key: int) -> Node | None:
        if node is None:
            return None
        if key < node.key:
            node.left = _delete(node.left, key)
        elif key > node.key:
            node.right = _delete(node.right, key)
        elif node.left is None:
            return node.right
        elif node.right is None:
            return node.left
        else:
            s = node.right
            while s.left is not None:
                s = s.left
            node.key = s.key
            node.right = _delete(node.right, s.key)
        return node

    self.root = _delete(self.root, key)
```

Реализация — по лекции 5. `search` спускается от корня циклом: меньший ключ — влево, больший — вправо. В `insert` и `delete` внутри метода — рекурсивная функция от поддерева: она возвращает новый корень поддерева, и родитель записывает его в свою ссылку. Метод вызывает её от корня (`self.root = _insert(self.root, key)`), поэтому удаление корня обрабатывается так же.

- `_insert`: спуск как при неудачном поиске, новый узел становится листом на месте пустой ссылки; равный ключ пропускается.
- `_delete`, **лист или один ребёнок**: если нет левого ребёнка, возвращается правый (у листа — `None`), и наоборот; ребёнок встаёт на место узла вместе с поддеревом.
- `_delete`, **два ребёнка**: преемник `s` — минимум правого поддерева; его ключ записывается в узел, затем `s.key` удаляется из правого поддерева. Левого ребёнка у `s` нет, поэтому это случай 1 или 2. Инвариант сохраняется: ключ `s` больше всех ключей левого поддерева и меньше остальных ключей правого.

Сложность:
- **Время:** O(h) у всех трёх операций, где h — высота дерева (один путь от корня вниз).
- **Память:** O(1) у `search`; у `insert` и `delete` — стек рекурсии глубины O(h).

Все три случая удаления проверяются в `self_check` (`check_delete`, `check_delete_two_children`), результаты — в разделе 4.

## 2. Обходы дерева

### 2.1. Реализация

```python
def in_order(self) -> list[int]:
    out: list[int] = []

    def walk(node: Node | None) -> None:
        if node is not None:
            walk(node.left)
            out.append(node.key)
            walk(node.right)

    walk(self.root)
    return out

def level_order(self) -> list[int]:
    out: list[int] = []
    queue = deque([self.root] if self.root is not None else [])
    while queue:
        node = queue.popleft()
        out.append(node.key)
        if node.left is not None:
            queue.append(node.left)
        if node.right is not None:
            queue.append(node.right)
    return out
```

Три рекурсивных обхода (по лекции 5) устроены одинаково: внутри метода — функция `walk`, которая дописывает ключи в общий список `out`, и вызов её от корня. Отличаются они только местом `out.append`: in-order — между вызовами для поддеревьев, pre-order — до них, post-order — после; `pre_order` и `post_order` в листинге не приведены. Level-order итеративный: корень кладётся в очередь `deque`, затем узел извлекается слева (`popleft`), его ключ записывается, а дети добавляются в конец очереди, пока она не опустеет. Поэтому узлы выходят по уровням, слева направо.

- **Время:** Θ(n) у каждого обхода, каждый узел посещается один раз.
- **Память:** результат Θ(n); у рекурсивных обходов — стек глубины O(h), у level-order — очередь до ≈ n/2 узлов (нижний уровень полного дерева).

### 2.2. Проверка

`check_traversals` из `self_check` сравнивает четыре обхода с известным ответом: пустое дерево (`[]`), идеальное дерево из вставок `4, 2, 6, 1, 3, 5, 7` и дерево лекции из вставок `8, 3, 10, 1, 6, 14, 4, 7, 13`:

| Обход | Дерево лекции |
| --- | --- |
| in-order | 1 3 4 6 7 8 10 13 14 |
| pre-order | 8 3 1 6 4 7 10 14 13 |
| post-order | 1 4 7 6 3 13 14 10 8 |
| level-order | 8 3 10 1 6 14 4 7 13 |

Результат — `обходы: OK`. С обходами заработали и проверки раздела 1, которые читают дерево через `in_order`/`pre_order`: `вставка и поиск: OK`, `удаление узла с двумя детьми: OK` (форма дерева после удаления совпадает с заменой преемником).
