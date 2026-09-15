class Solution(object):
    def twoSum(self, nums, target):
        dic = {}
        #for i in range(len(nums)):  # ← 这里就是bug
        for i,num in enumerate(nums):
            #num = nums[i]
            r = target - num
            if r in dic:
                return dic[r], i
            #else:
            dic[num] = i


# 测试
sol = Solution()
result = sol.twoSum([2, 7, 11, 15], 9)
print(result)  # 应该输出 (0, 1)