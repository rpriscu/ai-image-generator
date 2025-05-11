release: python verify_db.py && python downgrade_for_python_3_13.py && python setup_db.py --init
web: gunicorn run:app --config=gunicorn.conf.py
