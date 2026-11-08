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

## 3. Высота и число узлов

### 3.1. Реализация

```python
def height(self) -> int:
    def _height(node: Node | None) -> int:
        if node is None:
            return -1
        return 1 + max(_height(node.left), _height(node.right))

    return _height(self.root)

def size(self) -> int:
    def _size(node: Node | None) -> int:
        if node is None:
            return 0
        return 1 + _size(node.left) + _size(node.right)

    return _size(self.root)
```

Обе функции — post-order: узлу нужны результаты обоих поддеревьев, поэтому он обрабатывается после них. Высота узла — `1 + max` высот детей, у пустого поддерева `−1`, поэтому у листа выходит 0, а высота считается в рёбрах. Число узлов — 1 плюс размеры поддеревьев, у пустого 0.

- **Время:** Θ(n), каждый узел посещается один раз.
- **Память:** стек рекурсии O(h).

### 3.2. Проверка

`check_height_size` из `self_check`: пустое дерево — `−1` и 0, один узел — 0 и 1, идеальное дерево из 7 ключей — 2 и 7, дерево лекции — 3 и 9, цепочка из ключей `1, 2, …, 50` по возрастанию — 49 и 50. Результат — `высота и размер: OK`. С `height` и `size` заработали и последние проверки `self_check` (`удаление`, `сверка с эталоном set/sorted`), все шесть разделов проходят.

## 4. Верификация: инвариант BST и сверка с эталоном

### 4.1. Реализация

Сверку с эталоном делает `check_against_reference` из заготовки: 100 прогонов по 1–80 случайных команд `insert`/`delete` с ключами от −30 до 30 выполняются одновременно в дереве и в `set`. После каждой команды `in_order()` должен совпасть с `sorted(etalon)`; в конце прогона `search` сверяется с эталоном для всех ключей от −30 до 30 (есть и отсутствующие), `size()` — с `len(etalon)`, остальные обходы должны содержать те же ключи, а `height()` — лежать между `⌊log₂ n⌋` и `n − 1`.

Своя проверка — инвариант после каждой операции, двумя способами из лекции 5:

```python
def check_bst_invariant() -> None:
    def within(node: Node | None, low: float, high: float) -> bool:
        if node is None:
            return True
        return (
            low < node.key < high
            and within(node.left, low, node.key)
            and within(node.right, node.key, high)
        )

    inf = float("inf")
    broken = BST()
    broken.root = Node(5)
    broken.root.left, broken.root.right = Node(3), Node(8)
    broken.root.left.right = Node(7)
    got = broken.in_order()
    expect(got == [3, 7, 5, 8], f"in_order() дерева 5(3(-, 7), 8): {got}")
    expect(not within(broken.root, -inf, inf), "границы не поймали 7 слева от 5")

    rng = random.Random(1)
    for run in range(1, 101):
        tree = BST()
        for step in range(1, rng.randint(1, 80) + 1):
            k = rng.randint(-30, 30)
            op = "insert" if rng.random() < 0.6 else "delete"
            getattr(tree, op)(k)
            where = f"прогон {run}, команда №{step} {op}({k})"
            got = tree.in_order()
            expect(
                all(x < y for x, y in zip(got, got[1:])),
                f"{where}: in_order() не возрастает строго: {got}",
            )
            expect(
                within(tree.root, -inf, inf),
                f"{where}: ключ узла вне интервала, заданного предками",
            )
```

- `within` — рекурсия с границами: ключ узла должен лежать в интервале `(low, high)`, заданном предками; левый ребёнок получает верхнюю границу — ключ узла, правый — нижнюю.
- Строгое возрастание `in_order()` — проверка `is_bst` из лекции, без эталона.
- Сначала обе проверки запускаются на сломанном дереве со слайда 12 (у 3 правый ребёнок 7, хотя 7 лежит в левом поддереве 5): сравнение только с детьми его пропускает, а обе проверки должны отвергнуть. Затем — 100 прогонов случайных команд (свой seed), проверка после каждой команды.

### 4.2. Результат

```text
self_check:
  вставка и поиск: OK
  обходы: OK
  высота и размер: OK
  удаление: OK
  удаление узла с двумя детьми: OK
  сверка с эталоном set/sorted: OK
  инвариант BST после каждой операции: OK
self_check: OK
```

Чтобы убедиться, что проверки ловят ошибки, в `insert`/`delete` временно вносились типичные дефекты (из лекции 5) и запускался `self_check`:

| Дефект | Какие разделы `self_check` упали |
| --- | --- |
| удаление корня не меняет `self.root` | удаление, сверка с эталоном |
| при одном ребёнке поддерево теряется | удаление, удаление узла с двумя детьми, сверка с эталоном |
| преемник удаляется поиском от корня | все разделы с удалением — `RecursionError`: поиск снова находит тот же узел |
| ключ преемника скопирован, сам преемник не удалён | удаление, удаление узла с двумя детьми, сверка с эталоном, инвариант |
| равный ключ вставляется вправо (дубликаты) | вставка и поиск, сверка с эталоном, инвариант |

Проверка инварианта ловит только дефекты, ломающие порядок ключей (дубликаты). Потерянное поддерево или необновлённый корень оставляют корректное BST, но с другим набором ключей — их находит только сверка с эталоном. Поэтому нужны обе проверки.
