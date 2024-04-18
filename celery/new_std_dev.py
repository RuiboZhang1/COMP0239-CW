from tasks import power, mean, diff_vect, sq_vect

ages = [32,111,138,28,59,77,97]
mean_age = 0
result = mean.delay(ages)
while True: 
    if result.ready:
        mean_age = result.get()
        break
print(mean_age)

diff_ages = None
result = diff_vect.delay(mean_age, ages)
while True: 
    if result.ready:
        diff_ages = result.get()
        break
print(diff_ages)

sq_diffs = None
result = sq_vect.delay(diff_ages)
while True: 
    if result.ready:
        sq_diffs = result.get()
        break
print(sq_diffs)

variance = 0
result = mean.delay(sq_diffs)
while True: 
    if result.ready:
        variance = result.get()
        break
print(variance)

sq_rt = 0
result = power.delay(variance, 0.5)
while True: 
    if result.ready:
        sq_rt = result.get()
        break
print(sq_rt)