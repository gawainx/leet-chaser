# Advanced Case Types

Leet-Chaser 默认按 TOML 基础类型解析 `input` 和 `output`。当 LeetCode 题目用数组展示输入，但实际方法参数是链表或二叉树节点时，可以在 TOML 顶级增加类型元数据。

## 字段

```toml
input_types = ["linked_list", "raw"]
output_type = "linked_list"
```

- `input_types`：可选数组，位置和 `input` 参数一一对应。
- `output_type`：可选字符串，对应 `output`。
- `raw`：原样使用 TOML 基础类型。

支持的高级类型：

- `linked_list`：单链表，节点包含 `val` 和 `next`。
- `doubly_linked_list`：双向链表，节点包含 `val`、`prev` 和 `next`。
- `circular_linked_list`：循环单链表，节点包含 `val` 和 `next`。
- `binary_tree`：二叉树，节点包含 `val`、`left` 和 `right`。

## 单链表

```toml
entrypoint = "reverseList"
input_types = ["linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3, 4, 5]]
output = [5, 4, 3, 2, 1]
```

solution 收到的 `head` 是 `ListNode | None`。空数组会解析为 `None`。

```python
class Solution:
    def reverseList(self, head):
        previous = None
        current = head
        while current is not None:
            next_node = current.next
            current.next = previous
            previous = current
            current = next_node
        return previous
```

## 双向链表

```toml
entrypoint = "copy"
input_types = ["doubly_linked_list"]
output_type = "doubly_linked_list"

[[cases]]
input = [[1, 2, 3]]
output = [1, 2, 3]
```

solution 收到的节点包含 `prev` 和 `next`。比较输出时，Leet-Chaser 会从 head 沿 `next` 转回数组。

## 循环链表

循环链表使用 table 表示：

```toml
{ values = [3, 2, 0, -4], pos = 1 }
```

- `values`：节点值数组。
- `pos`：尾节点指向的节点下标。
- `pos = -1`：无环。

示例：

```toml
entrypoint = "identity"
input_types = ["circular_linked_list"]
output_type = "circular_linked_list"

[[cases]]
input = [{ values = [3, 2, 0, -4], pos = 1 }]
output = { values = [3, 2, 0, -4], pos = 1 }
```

当输出类型是 `circular_linked_list` 时，Leet-Chaser 会把实际返回值归一化为 `{ values = [...], pos = n }` 后比较，避免无限遍历。

## 二叉树

二叉树使用 LeetCode 层序数组表示。TOML 数组不能直接写 `null`，空节点使用字符串 `"null"`：

```toml
entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false
```

solution 收到的 `root` 是 `TreeNode | None`。空数组会解析为 `None`。

```python
class Solution:
    def isValidBST(self, root):
        def walk(node, lower, upper):
            if node is None:
                return True
            if not lower < node.val < upper:
                return False
            return walk(node.left, lower, node.val) and walk(node.right, node.val, upper)

        return walk(root, float("-inf"), float("inf"))
```

返回二叉树的题目可以声明 `output_type = "binary_tree"`：

```toml
entrypoint = "invertTree"
input_types = ["binary_tree"]
output_type = "binary_tree"

[[cases]]
input = [[4, 2, 7, 1, 3, 6, 9]]
output = [4, 7, 2, 9, 6, 3, 1]
```

比较输出时，Leet-Chaser 会把返回的 `TreeNode` 转回层序数组，并去掉末尾多余的 `"null"`。

## 混合参数

多个参数可以混合高级类型和 TOML 基础类型：

```toml
entrypoint = "rotateRight"
input_types = ["linked_list", "raw"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3, 4, 5], 2]
output = [4, 5, 1, 2, 3]
```

没有声明 `input_types` 或 `output_type` 时，行为和旧版本一致。

## 原地写入

数组原地修改类题目可以在 TOML 顶级声明原地写入比较：

```toml
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
```

- `inplace_write`：可选布尔值，默认 `false`。
- `inplace_index`：0-based 输入参数下标；`inplace_write = true` 时必填。

开启后，Leet-Chaser 会在调用 solution 后取 `input[inplace_index]` 作为实际结果，再和 `output` 比较。返回值会被忽略；如果返回值不是 `None`，`run` 和 `debug` 会打印 warning。
