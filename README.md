# Django Portfolio Website

A production-grade, reusable Django portfolio template with a dynamic, CMS-like structure and full admin capabilities. It ships with neutral placeholder content (the "Alex Morgan" persona) seeded via `populate_data` — replace it with your own from the Django admin (`/admin/`) without touching any code.

## 🚀 Features

### Core Features
- **Dynamic Content Management**: All content editable from Django admin
- **SEO Optimized**: Meta tags, Open Graph, sitemap.xml, RSS feeds
- **Responsive Design**: Mobile-friendly layouts
- **Contact Form**: Messages are saved to the database (viewable in the admin) with AJAX submission and toast feedback; email delivery is optional
- **Media Management**: Image uploads for projects, articles, and site settings

### Apps Structure
- **core**: Site settings, social links, SEO metadata
- **pages**: Homepage sections (about, skills, experience)
- **portfolio**: Projects and technologies with filtering
- **blog**: Articles, categories, tags with Markdown support

### Advanced Features
- **Pagination**: For blog articles and projects
- **RSS Feed**: Blog syndication at `/blog/feed/`
- **Sitemap**: Dynamic sitemap at `/sitemap.xml`
- **Markdown Rendering**: For blog articles (fenced code, tables, table of contents; install `Pygments` for code highlighting)
- **Search & Filters**: In admin and frontend
- **Slug-based URLs**: Clean, SEO-friendly URLs

## 🛠 Tech Stack

- **Backend**: Django 5.2+, Python 3.12+
- **Database**: SQLite by default (edit `DATABASES` in `portfolio_project/settings.py` to use PostgreSQL)
- **Frontend**: HTML5, CSS3, JavaScript, Three.js (animated 3D orb), Font Awesome
- **Admin**: Django Unfold theme, Django Summernote for rich text editing
- **Static files**: WhiteNoise (compressed, cache-busted)
- **Config**: `python-dotenv` (`.env` file)
- **Deployment**: Ready for Gunicorn + Nginx, or Passenger via `passenger_wsgi.py`

## 📦 Installation

### Prerequisites
- Python 3.12+
- pip package manager

### Setup Instructions

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/Viltrumlik/portfolio.git
   cd portfolio
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Then set at least your own `SECRET_KEY` in `.env` (see [Configuration](#-configuration)).

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate Initial Data**
   ```bash
   python manage.py populate_data
   ```
   Alternatively, `python manage.py populate_from_github [--user <github-username>] [--skip-cards]` loads the author's own curated content from `core/data/github_content.py` and merges in live repository data from the GitHub API (it also generates project preview cards). Edit `core/data/github_content.py` before using it for your own site.

8. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

9. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

10. **Access the Application**
   - Website: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## 🎯 Quick Start Guide

### 1. Configure Site Settings
1. Go to Admin → Core → Site Settings
2. Update your site name, hero title, and contact email
3. Upload your logo and favicon

### 2. Add Social Links
1. Go to Admin → Core → Social Links
2. Add your social media profiles with proper URLs

### 3. Create Skills
1. Go to Admin → Pages → Skills
2. Add your technical skills with proficiency levels
3. Group them by category (Frontend, Backend, Database, DevOps)

### 4. Add Projects
1. Go to Admin → Portfolio → Technologies
2. Add technologies you work with
3. Go to Admin → Portfolio → Projects
4. Create projects with descriptions, images, and links
5. Mark featured projects to appear on homepage

### 5. Write Blog Articles
1. Go to Admin → Blog → Categories
2. Create article categories
3. Go to Admin → Blog → Tags
4. Add relevant tags
5. Go to Admin → Blog → Articles
6. Write articles using Markdown or the rich text editor

### 6. Configure SEO
1. Go to Admin → Core → SEO
2. Set meta titles and descriptions for key pages

## 📁 Project Structure

```
portfolio/
├── portfolio_project/          # Main Django project
│   ├── settings.py             # Project settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── core/                       # Core app (settings, social links)
│   ├── models.py               # SiteSetting, SocialLink, SEO
│   ├── views.py                # HomePageView, ContactFormView
│   ├── admin.py                # Admin configuration
│   └── management/             # Custom management commands
├── pages/                      # Pages app (about, skills, experience)
│   ├── models.py               # Skill, Experience, AboutSection
│   ├── views.py                # AboutView, SkillsView, ExperienceView
│   └── admin.py                # Admin configuration
├── portfolio/                  # Portfolio app (projects)
│   ├── models.py               # Project, Technology
│   ├── views.py                # ProjectListView, ProjectDetailView
│   └── admin.py                # Admin configuration
├── blog/                       # Blog app (articles)
│   ├── models.py               # Article, Category, Tag
│   ├── views.py                # ArticleListView, ArticleDetailView
│   ├── admin.py                # Admin configuration
│   └── templatetags/           # Custom template tags
├── templates/                  # Django templates
│   ├── base.html               # Base template
│   ├── partials/               # Template partials
│   ├── core/                   # Core app templates
│   ├── pages/                  # Pages app templates
│   ├── portfolio/              # Portfolio app templates
│   └── blog/                   # Blog app templates
├── static/                     # Static files
│   ├── css/                    # CSS files (futuristic.css is the active theme)
│   ├── js/                     # JavaScript files (site-fx.js)
│   └── images/                 # Image files
├── public/
│   ├── static/                 # Collected static files (STATIC_ROOT)
│   └── media/                  # User uploaded files (MEDIA_ROOT)
├── passenger_wsgi.py           # Entry point for Passenger hosting
├── .env.example                # Environment variable template
└── requirements.txt
```

## 🔧 Configuration

Settings are read from environment variables, loaded from a `.env` file in the project root (copy `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | development key | Django secret key — always set your own |
| `DEBUG` | `True` | Set to `False` in production (enables secure cookies) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `CSRF_TRUSTED_ORIGINS` | empty | Comma-separated origins, e.g. `https://yourdomain.com` |
| `SECURE_SSL_REDIRECT` | `False` | Redirect HTTP to HTTPS when `DEBUG=False` |
| `EMAIL_BACKEND` | SMTP backend | Django email backend |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | `smtp.gmail.com` / `587` / `True` | SMTP server |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | empty | SMTP credentials; leave empty to disable email delivery |
| `DEFAULT_FROM_EMAIL` | `noreply@example.com` | Sender address |

### Email Settings (Contact Form)
Contact messages are always saved to the database. To also receive them by email, set the SMTP variables in `.env`:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Production Settings
For production deployment, set these in `.env`:

```bash
SECRET_KEY=<a-long-random-secret>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

The database is configured directly in `portfolio_project/settings.py` (SQLite by default). To use PostgreSQL, replace `DATABASES` there and install `psycopg`. Example `settings.py` changes for PostgreSQL and HSTS:

```python
# Database (PostgreSQL recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'portfolio_db',
        'USER': 'portfolio_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Security
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## 🚀 Deployment

### Using Gunicorn + Nginx

1. **Install Gunicorn** (already included in `requirements.txt`)
   ```bash
   pip install gunicorn
   ```

2. **Create Gunicorn Service**
   ```bash
   gunicorn portfolio_project.wsgi:application --bind 0.0.0.0:8000
   ```

3. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /static/ {
           alias /path/to/portfolio/public/static/;
       }
       
       location /media/ {
           alias /path/to/portfolio/public/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Using Passenger (shared hosting)
`passenger_wsgi.py` exposes the WSGI application for Passenger-based hosts (for example Serv00). It adds a `venv`/`.venv` in the project or home directory to `sys.path` and writes startup errors to `passenger_debug.log`.

### Using Docker
Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "portfolio_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📝 Customization Guide

### Adding New Sections
1. Create new models in appropriate app
2. Update admin configuration
3. Create views and templates
4. Add URL patterns

### Modifying Design
- Edit `static/css/futuristic.css` for the active theme (loaded by `templates/base.html`)
- Edit `static/js/site-fx.js` for front-end effects (the Three.js orb and animations)
- Update templates in `templates/` directory

### Adding New Apps
1. `python manage.py startapp new_app`
2. Add to `INSTALLED_APPS` in settings
3. Configure URLs, models, views, templates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

Third-party assets loaded from CDNs (Three.js, Font Awesome, Google Fonts) keep their own licenses.

## 🆘 Support

If you encounter any issues:

1. Check the Django documentation
2. Review the error logs
3. Ensure all dependencies are installed
4. Verify static files are collected: `python manage.py collectstatic`
5. Clear browser cache and restart development server

## 🔄 Updates

To update the project:

1. Backup your database
2. Pull latest changes
3. Run migrations: `python manage.py migrate`
4. Collect static files: `python manage.py collectstatic`
5. Restart the server

## 📊 Performance Tips

- Use PostgreSQL in production
- Enable Django caching
- Optimize images before uploading
- Use CDN for static files in production
- Enable database connection pooling
- Monitor and optimize database queries

---

**Happy Coding! 🎉**
