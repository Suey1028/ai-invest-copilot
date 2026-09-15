class Solution:
    def isValid(self, s: str) -> bool:
        """判断括号字符串是否有效"""
        stack=[]
        pairs={")":"(","}":"{","]":"["}
        #left=["[","{","("] 用paris的派生可以解决
        for m in s:
            # if m in left:
            #     stack.append(m)
            if m in pairs:
                if not stack:
                    return False
                top=stack.pop()
                if top!=pairs[m]:
                     return False
            else:
                stack.append(m)
        # if not stack:
        #     return True
        # else:
        #     return False
        return not stack


# 测试用例
sol = Solution()
test_cases = [
    ("()", True),
    ("()[]{}", True),
    ("(]", False),
    ("([)]", False),
    ("{[]}", True),
    ("", True),
    ("]",False),
    ("(", False),
]

for s, expected in test_cases:
    result = sol.isValid(s)
    status = "✅" if result == expected else "❌"
    print(f"{status} isValid({s!r}) = {result}, expected {expected}")

