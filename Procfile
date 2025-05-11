release: python downgrade_for_python_3_13.py && python setup_db.py --init && python verify_heroku.py
web: gunicorn run:app --config=gunicorn.conf.py
