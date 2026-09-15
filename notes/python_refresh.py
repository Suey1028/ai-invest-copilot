"""Python语法快速回顾（30分钟）
玩法：读每一段代码 → 按注释里的"你来做"要求改一下 → 运行看结果
"""

# ==================== 1. 变量与基础类型 ====================
# 数字、字符串、布尔
age = 24
name = "Suey"
is_student = True

# f-string（Python最常用的字符串格式化）
print(f"我叫{name}，今年{age}岁，学生身份：{is_student}")

# 你来做：把age改成你的实际年龄，重新运行
age_new=22
name_new="杨穗瑜"
is_student_new=False
print(f"my name is {name_new}, I am {age_new} years old")

# ==================== 2. 列表（最高频数据结构） ====================
fruits = ["apple", "banana", "cherry"]

# 常用操作
print(fruits[0])           # 索引：apple
print(fruits[-1])          # 倒数索引：cherry
print(len(fruits))         # 长度：3
fruits.append("orange")    # 追加
fruits.remove("banana")    # 删除
print(fruits)              # ['apple', 'cherry', 'orange']

# 列表推导式（Python最优雅的语法之一）
squares = [x**2 for x in range(5)]
print(squares)             # [0, 1, 4, 9, 16]

# 你来做：写一个列表推导式，生成 1-10 的偶数列表
oushu=[x for x in range(1,11) if x%2==0]
print(oushu)


# ==================== 3. 字典（第二高频数据结构） ====================
stock = {
    "code": "600519.SH",
    "name": "贵州茅台",
    "price": 1330.00
}

# 常用操作
print(stock["name"])                     # 贵州茅台
stock["volume"] = 37108                  # 新增key
print(stock.get("dividend", 0))          # 安全获取（key不存在返回默认值0）
print(stock.keys())                      # 所有key
print(stock.values())                    # 所有value

# 遍历字典
for key, value in stock.items():
    print(f"{key}: {value}")

# 你来做：新建一个字典表示你自己（姓名、年龄、学校），并遍历打印
personal_info={"name":"Suey","age":22,"school":"HKU"}
print(f"{personal_info['name']}的学校是{personal_info['school']}")
for key,value in personal_info.items():
    print(f"{key}:{value}")
# ==================== 4. 循环与条件 ====================
# for循环
for i in range(3):
    print(f"第{i+1}次循环")

# if-elif-else
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
print(f"得分{score}，等级{grade}")

# 你来做：写一个for循环，遍历fruits列表，如果长度大于5打印"长名字"，否则打印"短名字"
fruit=["香蕉","苹果","火龙果","奇异果"]
len_fruit=len(fruit)
if len_fruit>5:
    print("长名字")
else:
    print("短名字")

# ==================== 5. 函数（工程代码的核心） ====================
def calculate_return(start_price, end_price):
    """计算收益率"""
    return (end_price - start_price) / start_price

# 调用函数
rate = calculate_return(100, 110)
print(f"收益率：{rate:.2%}")  # 10.00%

# 多返回值（其实是返回元组）
def get_stats(prices):
    return max(prices), min(prices), sum(prices) / len(prices)

high, low, avg = get_stats([10, 20, 30, 40])
print(f"最高{high}, 最低{low}, 平均{avg}")

# 你来做：写一个函数，输入两个价格，返回一个字典 {"收益率": xx, "涨跌": xx}
# （提示：涨返回"涨"，跌返回"跌"）
def t(be,af):
    rate=(af-be)/be
    result={"收益率":rate,"涨跌":"涨" if rate>0 else "跌"}
    return result
fin=t(10,20)
print(fin)


# ==================== 6. 异常处理 ====================
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        print("不能除以0！")
        return None
    except TypeError:
        print("类型错误！")
        return None

print(safe_divide(10, 2))    # 5.0
print(safe_divide(10, 0))    # None（打印错误提示）
print(safe_divide(10, "a"))  # None


# ==================== 7. 装饰器（Day 5实战会用） ====================
import time
from functools import wraps

def timer(func):
    """装饰器：打印函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[{func.__name__}] 耗时: {elapsed:.4f}秒")
        return result
    return wrapper

# 使用装饰器
@timer
def slow_function():
    time.sleep(0.5)
    return "完成"

slow_function()  # [slow_function] 耗时: 0.5023秒

# ==================== 补课：*args 和 **kwargs ====================

def show_all(*args, **kwargs):
    """演示 *args 和 **kwargs 的打包效果"""
    print(f"args 打包成元组：{args}")
    print(f"kwargs 打包成字典：{kwargs}")

show_all(1, 2, 3, name="Suey", age=22)
# 输出：
# args 打包成元组：(1, 2, 3)
# kwargs 打包成字典：{'name': 'Suey', 'age': 22}

# ==================== 补课：装饰器 ====================
import time
from functools import wraps

def timer(func):
    """装饰器：打印函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[{func.__name__}] 耗时：{elapsed:.4f}秒")
        return result
    return wrapper


@timer
def slow_task():
    """模拟一个慢任务"""
    time.sleep(0.5)
    return "任务完成"

result = slow_task()
print(f"结果：{result}")
# 输出：
# [slow_task] 耗时：0.5020秒
# 结果：任务完成