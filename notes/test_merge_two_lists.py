from typing import Optional


# LeetCode默认给的节点定义
class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(
        self,
        list1: Optional[ListNode],
        list2: Optional[ListNode],
    ) -> Optional[ListNode]:
        """合并两个升序链表，返回合并后的升序链表头节点。"""
        # 在这里写你的双指针 + 虚拟头节点逻辑
        dummy=ListNode(0)
        current=dummy
        while list1 and list2:
            if list1.val>=list2.val:
                current.next=list2
                list2=list2.next
            else:
                current.next=list1
                list1=list1.next
            current=current.next
        # while list1:
        #     current.next=list1
        #     list1=list1.next
        #     current=current.next
        # while list2:
        #     current.next=list2
        #     list2=list2.next
        #     current=current.next
        current.next=list1 if list1 else list2
        return dummy.next#ummy 变量一直指向 ListNode(0)，ListNode(0) 的 next 字段"被 current 改了

# ============ 工具函数 ============
def list_to_linked(nums: list[int]) -> Optional[ListNode]:
    """把Python list转成链表（方便测试）。"""
    if not nums:
        return None
    dummy = ListNode(0)
    current = dummy
    for num in nums:
        current.next = ListNode(num)
        current = current.next
    return dummy.next


def linked_to_list(head: Optional[ListNode]) -> list[int]:
    """把链表转回Python list（方便验证）。"""
    result = []
    current = head
    while current is not None:
        result.append(current.val)
        current = current.next
    return result


# ============ 测试用例 ============
sol = Solution()
test_cases = [
    ([1, 2, 4], [1, 3, 4], [1, 1, 2, 3, 4, 4]),   # 普通case
    ([], [], []),                                    # 双空
    ([], [0], [0]),                                  # 一空
    ([1], [2], [1, 2]),                              # 都只有一个
    ([1, 2, 3], [4, 5, 6], [1, 2, 3, 4, 5, 6]),    # 一堆比另一堆全小
    ([2], [1], [1, 2]),                              # 顺序颠倒
]

for nums1, nums2, expected in test_cases:
    list1 = list_to_linked(nums1)
    list2 = list_to_linked(nums2)
    merged = sol.mergeTwoLists(list1, list2)
    result = linked_to_list(merged)
    status = "✅" if result == expected else "❌"
    print(f"{status} merge({nums1}, {nums2}) = {result}, expected {expected}")