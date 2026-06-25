# Render Deployment Guide for Nyveralife

## Prerequisites
1. GitHub account with your code pushed to: https://github.com/jahidulislamseo/shop
2. Render account (sign up at https://render.com - free tier available)

## Step-by-Step Deployment

### 1. Sign Up/Login to Render
- Go to https://render.com
- Sign up with your GitHub account
- Authorize Render to access your repositories

### 2. Create a New Web Service
1. Click "New +" button
2. Select "Web Service"
3. Connect your GitHub repository: `jahidulislamseo/shop`
4. Click "Connect"

### 3. Configure Web Service

**Basic Settings:**
- **Name**: `nyveralife-bd` (or your preferred name)
- **Region**: Choose closest to Bangladesh (Singapore recommended)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn config.wsgi:application`

**Instance Type:**
- Select "Free" tier (for testing)
- Upgrade to paid tier for production use

### 4. Add Environment Variables

Click "Advanced" and add these environment variables:

```
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=.onrender.com
DATABASE_URL=(will be auto-filled by Render PostgreSQL)
DISABLE_COLLECTSTATIC=1
```

### 5. Create PostgreSQL Database

1. Go back to Render Dashboard
2. Click "New +" → "PostgreSQL"
3. **Name**: `nyveralife-bd-db`
4. **Database**: `nyveralifebd`
5. **User**: `nyveralifebd_user`
6. **Region**: Same as web service
7. **PostgreSQL Version**: 15
8. Click "Create Database"

### 6. Link Database to Web Service

1. Go to your Web Service settings
2. In Environment Variables, add:
   - **Key**: `DATABASE_URL`
   - **Value**: Copy the "Internal Database URL" from your PostgreSQL database

### 7. Deploy!

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start the server

### 8. Post-Deployment Setup

Once deployed, you need to create a superuser:

1. Go to your Web Service
2. Click "Shell" tab
3. Run:
```bash
python manage.py createsuperuser
```

### 9. Access Your Live Website

Your website will be available at:
```
https://nyveralife-bd.onrender.com
```

Admin panel:
```
https://nyveralife-bd.onrender.com/manager-portal-631/
```

## Important Notes

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- 750 hours/month free (enough for one service)

### For Production Use
1. Upgrade to paid tier ($7/month)
2. Add custom domain
3. Enable SSL (automatic with Render)
4. Set up email service (SendGrid, Mailgun)
5. Configure SSLCommerz for payments

### Static Files
- Render serves static files automatically
- Media files need external storage (AWS S3, Cloudinary)

### Database Backups
- Render provides automatic backups on paid plans
- Free tier: Manual backups recommended

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure `build.sh` has execute permissions

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL database is running
- Ensure web service and database are in same region

### Static Files Not Loading
- Run `python manage.py collectstatic` manually
- Check `STATIC_ROOT` and `STATIC_URL` in settings
- Verify `whitenoise` is installed

### 500 Errors
- Check application logs in Render dashboard
- Verify all environment variables are set
- Check `DEBUG=False` and `ALLOWED_HOSTS` includes `.onrender.com`

## Updating Your Site

After making changes:
1. Commit and push to GitHub:
```bash
git add .
git commit -m "Your update message"
git push origin main
```

2. Render will automatically detect changes and redeploy

## Custom Domain Setup

1. Go to Web Service settings
2. Click "Custom Domains"
3. Add your domain
4. Update DNS records as instructed
5. SSL certificate will be auto-generated

## Support

For issues:
- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Django Deployment: https://docs.djangoproject.com/en/5.1/howto/deployment/

---

**Your Nyveralife will be live in ~5-10 minutes after deployment starts!** 🚀
