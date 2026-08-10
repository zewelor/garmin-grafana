test_dockerignore:
  rsync -avn . /dev/shm --exclude-from .dockerignore
