workers = 4
bind = '0.0.0.0:8000'
threads = 2  # Number of threads per worker
preload_app = True  # Preload the application code before the worker processes are forked
