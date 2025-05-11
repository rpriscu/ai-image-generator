release: python downgrade_for_python_3_13.py && python create_tables.py && python setup_db.py --create-admin
web: gunicorn run:app --config=gunicorn.conf.py
