### For start flower
celery --broker=redis://localhost:6379/1 flower --basic_auth=user1:password1
### For start celery
celery -A main.celery worker --loglevel=INFO