import random
import time



start = time.time()



ary = []
xxx = 10000000
for r in range(xxx):
    ary.append(random.randint(0,xxx))

end = time.time()
print("generate random ary", end - start)


def counting_sort(array, maxval):
    """in-place counting sort"""
    m = maxval + 1
    count = [0] * m               # init with zeros
    for a in array:
        count[a] += 1             # count occurences
    i = 0
    for a in range(m):            # emit
        for c in range(count[a]): # - emit 'count[a]' copies of 'a'
            array[i] = a
            i += 1
    return array


# ------------------------------------
# counting sort
new_copy = ary.copy()
#print("new_copy: ", new_copy)
start = time.time()
counting_sort(new_copy, xxx)
end = time.time()
print("counting sort", end - start)
# end counting sort

# ------------------------------------
# counting sort
new_copy = ary.copy()
#print("new_copy: ", new_copy)
start = time.time()
sorted(new_copy)
end = time.time()
print("sorted", end - start)
# end counting sort
