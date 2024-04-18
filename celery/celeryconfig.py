broker_url = 'redis://10.0.15.46:6379/0'  # Host's internal IP
result_backend = 'redis://10.0.15.46:6379/1'  # Host's internal IP
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
