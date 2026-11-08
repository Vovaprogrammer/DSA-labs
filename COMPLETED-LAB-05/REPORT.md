# Отчёт по ЛР 5. Бинарное дерево поиска: обходы, вставка и удаление

**Вариант:** N = `14`
**Seed:** `30 + 14 = 44`
**Окружение:** Python `3.11`, CPU `12th Gen Intel(R) Core(TM) i5-12400F — 6 ядер.`

Код — в файле `lab-05-bst.py`, запуск: `python COMPLETED-LAB-05/lab-05-bst.py --variant 14`.
Код отформатирован `black` и проверен `pylint`.

## 1. Вставка, поиск и удаление

```python
def _insert(node: Node | None, key: int) -> Node:
    if node is None:
        return Node(key)
    if key < node.key:
        node.left = _insert(node.left, key)
    elif key > node.key:
        node.right = _insert(node.right, key)
    return node


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


class BST:
    def insert(self, key: int) -> None:
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
        self.root = _delete(self.root, key)
```

Реализация — по лекции 5. `search` спускается от корня циклом: меньший ключ — влево, больший — вправо. `_insert` и `_delete` — рекурсивные функции от поддерева, они возвращают его новый корень, и родитель записывает этот корень в свою ссылку. Поэтому методы класса выглядят как `self.root = _insert(self.root, key)`, и удаление корня обрабатывается так же.

- `_insert`: спуск как при неудачном поиске, новый узел становится листом на месте пустой ссылки; равный ключ пропускается.
- `_delete`, **лист или один ребёнок**: если нет левого ребёнка, возвращается правый (у листа — `None`), и наоборот; ребёнок встаёт на место узла вместе с поддеревом.
- `_delete`, **два ребёнка**: преемник `s` — минимум правого поддерева; его ключ записывается в узел, затем `s.key` удаляется из правого поддерева. Левого ребёнка у `s` нет, поэтому это случай 1 или 2. Инвариант сохраняется: ключ `s` больше всех ключей левого поддерева и меньше остальных ключей правого.

Сложность:
- **Время:** O(h) у всех трёх операций, где h — высота дерева (один путь от корня вниз).
- **Память:** O(1) у `search`; у `insert` и `delete` — стек рекурсии глубины O(h).

Все три случая удаления проверяются в `self_check` (`check_delete`, `check_delete_two_children`), результаты — в разделе 4.
