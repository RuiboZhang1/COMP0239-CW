from weatherTasks import getWeatherData, parseData, fitData
from celery import chain

cities = ['london', 'madrid', 'newyork', 'shanghai']
results = []
for city in cities:
    results.append(chain(getWeatherData.s(city), parseData.s(), fitData.s())())

for result in results:
    print(result.get())