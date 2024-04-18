workers = 4
bind = '127.0.0.1:8000'
threads = 4  # Number of threads per worker
preload_app = True  # Preload the application code before the worker processes are forked
