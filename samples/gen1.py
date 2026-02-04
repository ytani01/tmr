import time


def gen1():
    i = 0
    while True:
        yield i
        time.sleep(2)
        i += 1


for j in gen1():
    print(j)
    if j > 2:
        break
