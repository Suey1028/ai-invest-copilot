from typing import List


class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        """原地删除有序数组的重复项，返回去重后的新长度。
        
        要求：数组前k个位置必须是去重后的元素，后面的不管。
        """
        # # 在这里写你的双指针逻辑
        # if len(nums)==1:
        #     return 1
        # only_nums=[]
        # for i in range(len(nums)):
        #     if nums[i] not in only_nums:
        #         only_nums.append(nums[i])
        #     #else:
        #     #    del nums[i]
        # return len(only_nums)
        if not nums:
            return 0
        slow=0
        for i in range(1,len(nums)):
            if nums[slow]==nums[i]:
                continue
            slow+=1
            nums[slow]=nums[i]
        return slow+1


# 测试用例
sol = Solution()
test_cases = [
    ([1, 1, 2], 2, [1, 2]),
    ([0, 0, 1, 1, 1, 2, 2, 3, 3, 4], 5, [0, 1, 2, 3, 4]),
    ([1], 1, [1]),
    ([1, 2, 3], 3, [1, 2, 3]),   # 无重复
    ([1, 1, 1, 1], 1, [1]),      # 全部重复
]

for nums, expected_k, expected_front in test_cases:
    nums_copy = nums.copy()
    k = sol.removeDuplicates(nums_copy)
    front = nums_copy[:k]
    status = "✅" if k == expected_k and front == expected_front else "❌"
    print(f"{status} removeDuplicates({nums}) k={k}, front={front}, expected k={expected_k}, front={expected_front}")