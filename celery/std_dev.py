from tasks import add, divide, multiply, subtract, power

ages = [32,111,138,28,59,77,97]

sum = 0
for value in ages:
    result = add.delay(sum, value)
    while True: 
        if result.ready:
            sum = result.get()
            break
print(sum)

mean = 0
result = divide.delay(sum, len(ages))
while True: 
    if result.ready:
        mean = result.get()
        break
print(mean)

errors = []
for value in ages:
    result = subtract.delay(value, mean)
    while True: 
        if result.ready:
            errors.append(result.get())
            break
print(errors)

sqs = []
for err in errors:
    result = power.delay(err, 2)
    while True: 
        if result.ready:
            sqs.append(result.get())
            break
print(sqs)

sqs_sum = 0
for value in sqs:
    result = add.delay(sqs_sum, value[0])
    while True: 
        if result.ready:
            sqs_sum = result.get()
            break
print(sqs_sum)

variance = 0
result = divide.delay(sqs_sum, len(ages))
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