# Deployment Guide for Heroku

This guide provides step-by-step instructions for deploying the AI Image Generator application to Heroku using Python 3.13.

## Prerequisites

1. [Heroku account](https://signup.heroku.com/) (verified with a credit card for add-ons)
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
3. [Git](https://git-scm.com/downloads) installed
4. GitHub account (optional, for GitHub integration)

## 1. Prepare the Application

Ensure your application has the following files in the root directory:

- `Procfile` with content: `web: gunicorn run:app --config=gunicorn.conf.py`
- `.python-version` with content: `3.13`
- `requirements.txt` with all dependencies
- `gunicorn.conf.py` for web server configuration

## 2. Login to Heroku

Open a terminal and login to Heroku:

```bash
heroku login
```

## 3. Create a Heroku App

Create a new Heroku application:

```bash
heroku create your-app-name
```

Or if you want Heroku to generate a name for you:

```bash
heroku create
```

## 4. Set Environment Variables

Set the necessary environment variables for your application:

```bash
# Flask configuration
heroku config:set SECRET_KEY=your_secure_random_key
heroku config:set FLASK_ENV=production

# FAL.ai API configuration
heroku config:set FAL_KEY=your_fal_api_key

# Google OAuth configuration (if using)
heroku config:set GOOGLE_CLIENT_ID=your_google_client_id
heroku config:set GOOGLE_CLIENT_SECRET=your_google_client_secret
heroku config:set ALLOWED_EMAIL_DOMAIN=zemingo.com

# Admin user credentials
heroku config:set ADMIN_USERNAME=admin
heroku config:set ADMIN_PASSWORD=secure_admin_password

# Add the app name for proper URL generation
heroku config:set HEROKU_APP_NAME=your-app-name

# Performance tuning (optional)
heroku config:set WEB_CONCURRENCY=2
heroku config:set GUNICORN_THREADS=2
```

## 5. Provision a Postgres Database

Add a PostgreSQL database to your application:

```bash
heroku addons:create heroku-postgresql:mini
```

## 6. (Optional) Add Redis for Session Storage

For more reliable session storage on Heroku's ephemeral filesystem, you can add Redis:

```bash
heroku addons:create heroku-redis:mini
```

## 7. Deploy the Application

There are two ways to deploy your application to Heroku:

### Option 1: Deploy directly from your local Git repository

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### Option 2: Deploy through GitHub integration

1. Push your code to a GitHub repository
2. In the Heroku Dashboard, go to your app → Deploy tab
3. Connect your GitHub repository
4. Choose the branch to deploy
5. Click "Deploy Branch" or enable "Automatic Deploys"

## 8. Initialize the Database

After deployment, run the database setup:

```bash
heroku run python setup_db.py --init
heroku run python setup_db.py --create-admin
```

## 9. Open the Application

Open your application in the browser:

```bash
heroku open
```

## Monitoring and Troubleshooting

### View Logs

```bash
heroku logs --tail
```

### Access the Heroku Shell

```bash
heroku run bash
```

### Check Dyno Status

```bash
heroku ps
```

### Database Management

Access your PostgreSQL database:

```bash
heroku pg:psql
```

### Redis Management (if using)

Monitor Redis usage:

```bash
heroku redis:info
```

## Updating the Application

To update your application:

1. Make changes to your code
2. Commit your changes: `git commit -am "Update feature X"`
3. Push to Heroku: `git push heroku main`

## Scaling the Application

To scale your application:

```bash
# Scale web dynos
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1
```

## Database Backups

Create a backup of your database:

```bash
heroku pg:backups:capture
```

Download a backup:

```bash
heroku pg:backups:download
```

## Production Best Practices

1. **Monitor your application**: Set up New Relic or other monitoring tools
2. **Set up alerting**: Configure alerts for application errors
3. **Regular backups**: Schedule regular database backups
4. **Security updates**: Keep dependencies updated
5. **Custom domain**: Configure a custom domain for your application
6. **SSL**: Enable SSL for secure connections

## Additional Resources

- [Heroku Dev Center - Python Support](https://devcenter.heroku.com/articles/python-support)
- [Heroku Dev Center - Getting Started with Python](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Heroku Dev Center - Postgres](https://devcenter.heroku.com/articles/heroku-postgresql)
- [Heroku Dev Center - Redis](https://devcenter.heroku.com/articles/heroku-redis) 