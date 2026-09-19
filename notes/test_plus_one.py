from typing import List


class Solution:
    def plusOne(self, digits: List[int]) -> List[int]:
        """给数组表示的非负整数加1，返回新数组。"""
        # last_num=digits[-1]
        # if last_num!=9:
        #     digits[-1]=last_num+1
        #     return digits
        # else:
        #len_digits=len(digits)#可以不用再赋值
        #for i in range(len_digits-1,-1,-1):
        for i in reversed(range(len(digits))):#更简单的写法
            #last_num=digits[i]#可以不用这个变量
            #if last_num!=9:
            if digits[i]!=9:
                digits[i]+=1
                #digits[i]=last_num+1
                return digits
            else:
                digits[i]=0
                if i==0:
                    return [1]+digits

# 测试用例
sol = Solution()
test_cases = [
    ([1, 2, 3], [1, 2, 4]),         # 普通case
    ([4, 3, 2, 1], [4, 3, 2, 2]),  # 普通case
    ([9], [1, 0]),                  # 单一9进位
    ([9, 9, 9], [1, 0, 0, 0]),     # 全9进位
    ([1, 2, 9], [1, 3, 0]),        # 中间进位
    ([0], [1]),                     # 边界：0 + 1
]

for digits, expected in test_cases:
    result = sol.plusOne(digits.copy())  # 传副本避免污染原数组
    status = "✅" if result == expected else "❌"
    print(f"{status} plusOne({digits}) = {result}, expected {expected}")