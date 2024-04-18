from tasks import power, mean, diff_vect, sq_vect
from celery import signature, chain

ages = [32,111,138,28,59,77,97]
sq_rt_partial = power.s(0.5)  
# result = chain( mean.s(ages), diff_vect.s(ages), sq_vect.s(), mean.s())()
result = chain( mean.s(ages), diff_vect.s(ages), sq_vect.s(), mean.s(), sq_rt_partial)()
print(result.get())