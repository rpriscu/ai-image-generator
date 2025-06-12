# Temporarily disabled release command to force deployment
# release: python scripts/utils/downgrade_for_python_3_13.py && python scripts/utils/create_tables.py && python scripts/utils/setup_db.py --create-admin
web: gunicorn run:app --config=gunicorn.conf.py
worker: python worker.py
