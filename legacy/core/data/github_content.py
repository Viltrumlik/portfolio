"""
Curated, English content for the guts.uz portfolio, authored from the GitHub
profile and repository READMEs of A1isherDev (Alisher Muhammadaliyev).

This is the human-written layer that the `populate_from_github` management command
merges with live GitHub metadata (languages, avatar, repo URLs). Descriptions for
projects whose repos have no/Uzbek README were summarised/translated to English.
Everything here is safe to edit from code or override in the Django admin.
"""

GITHUB_USER = "A1isherDev"
AVATAR_URL = "https://avatars.githubusercontent.com/u/204816162?v=4"

# ── Identity (SiteSetting + AboutSection) ──────────────────────────────────────
IDENTITY = {
    "site_name": "Alisher Muhammadaliyev",
    "hero_title": "I'm Alisher Muhammadaliyev",
    "hero_subtitle": "Backend Developer & Software Engineer",
    "hero_greeting": "👋 Hello, I am",
    "hero_description": (
        "I'm a backend developer from Fergana, Uzbekistan. I build reliable "
        "server-side systems, REST APIs and bots with Python, Django and "
        "PostgreSQL — turning ideas into clean, scalable products, from Telegram "
        "bots to full learning platforms."
    ),
    "contact_email": "Alishermuhammadaliyev2508@gmail.com",
    "location": "Fergana, Uzbekistan",
    "company": "Najot Ta'lim",
    # AboutSection
    "about_title": "About Me",
    "about_content": (
        "<p>I'm Alisher Muhammadaliyev, a backend developer and software engineer "
        "from Fergana, Uzbekistan. I build reliable server-side systems, REST APIs "
        "and bots, mostly with Python, Django and PostgreSQL.</p>"
        "<p>I'm currently sharpening my backend skills at Najot Ta'lim while shipping "
        "real projects — from a volunteer-management Telegram bot and a Digital SAT "
        "learning platform to a kids' financial-literacy game. I care about clean "
        "architecture, readable code, and turning ideas into working products.</p>"
        "<p>I'm always learning and “locked in” on becoming a better "
        "engineer every day.</p>"
    ),
    "education": "Backend Development @ Najot Ta'lim",
    "languages_spoken": "Uzbek, English, Russian",
    "years_experience": "2+",
    "projects_completed": "13+",
    "happy_clients": "5+",
}

# ── Social links (platform_name must match SocialLink.PLATFORM choices) ─────────
SOCIALS = [
    ("github", "https://github.com/A1isherDev", "fab fa-github", 1),
    ("linkedin", "https://www.linkedin.com/in/alisher-muhammadaliyev-616795344", "fab fa-linkedin-in", 2),
    ("telegram", "https://t.me/Alisher_Muhammadaliyev", "fab fa-telegram", 3),
    ("instagram", "https://www.instagram.com/a1isherdev", "fab fa-instagram", 4),
    ("twitter", "https://x.com/A1isherDev", "fab fa-x-twitter", 5),
    ("facebook", "https://www.facebook.com/profile.php?id=61574860190522", "fab fa-facebook-f", 6),
    ("discord", "https://discord.com/users/1354328698454675500", "fab fa-discord", 7),
]

# ── Skills (name, group, level, icon_class) ────────────────────────────────────
SKILLS = [
    ("Python", "backend", 90, "fab fa-python"),
    ("Django", "backend", 88, "fas fa-server"),
    ("Django REST Framework", "backend", 82, "fas fa-network-wired"),
    ("C++", "backend", 70, "fas fa-code"),
    ("Node.js", "backend", 60, "fab fa-node-js"),
    ("PostgreSQL", "database", 80, "fas fa-database"),
    ("SQLite", "database", 78, "fas fa-database"),
    ("Redis", "database", 65, "fas fa-database"),
    ("HTML5", "frontend", 90, "fab fa-html5"),
    ("CSS3", "frontend", 85, "fab fa-css3-alt"),
    ("JavaScript", "frontend", 75, "fab fa-js"),
    ("TypeScript", "frontend", 66, "fab fa-js"),
    ("Bootstrap", "frontend", 80, "fab fa-bootstrap"),
    ("Docker", "devops", 72, "fab fa-docker"),
    ("Git", "devops", 88, "fab fa-git-alt"),
    ("Linux", "devops", 75, "fab fa-linux"),
    ("Telegram Bots (aiogram)", "other", 82, "fab fa-telegram"),
    ("Flutter / Dart", "other", 55, "fas fa-mobile-screen-button"),
]

# ── Technology icon map (Font Awesome). Unmapped → template falls back to code ──
TECH_ICONS = {
    "Python": "fab fa-python",
    "Django": "fas fa-server",
    "Django REST Framework": "fas fa-network-wired",
    "PostgreSQL": "fas fa-database",
    "SQLite": "fas fa-database",
    "Redis": "fas fa-database",
    "Celery": "fas fa-bolt",
    "JavaScript": "fab fa-js",
    "TypeScript": "fab fa-js",
    "HTML": "fab fa-html5",
    "CSS": "fab fa-css3-alt",
    "SCSS": "fab fa-sass",
    "PHP": "fab fa-php",
    "Node.js": "fab fa-node-js",
    "React": "fab fa-react",
    "Next.js": "fas fa-layer-group",
    "Tailwind CSS": "fas fa-wind",
    "Bootstrap": "fab fa-bootstrap",
    "Docker": "fab fa-docker",
    "Dart": "fas fa-mobile-screen-button",
    "Flutter": "fas fa-mobile-screen-button",
    "Material Design": "fas fa-mobile-screen-button",
    "Java": "fab fa-java",
    "Kotlin": "fas fa-code",
    "C++": "fas fa-code",
    "Shell": "fas fa-terminal",
    "aiogram": "fab fa-telegram",
    "SQLAlchemy": "fas fa-database",
    "Alembic": "fas fa-database",
    "JWT": "fas fa-key",
    "Git": "fab fa-git-alt",
    "Gunicorn": "fas fa-server",
    "Nginx": "fas fa-server",
    "WhiteNoise": "fas fa-feather",
}

# Languages returned by the GitHub API that we don't want shown as tech tags,
# plus renames to canonical names.
LANG_DROP = {"Mako"}
LANG_RENAME = {"Dockerfile": "Docker"}

# ── Projects (keyed by GitHub repo name) ───────────────────────────────────────
# extra_tech = frameworks/tools not reported by the languages API.
PROJECTS = {
    "LMS_SATFergana": {
        "title": "SAT LMS Platform",
        "short_description": (
            "A full learning management system for Digital SAT prep — practice tests, "
            "question banks, analytics, and teacher tools."
        ),
        "long_description": (
            "SAT LMS is a comprehensive learning management system built specifically "
            "for Digital SAT exam preparation. Students get full-length, Bluebook-style "
            "practice tests, an extensive question bank organised by subject and "
            "difficulty, spaced-repetition flashcards, homework tracking, peer rankings, "
            "and a personal analytics dashboard that highlights weak areas.\n\n"
            "Teachers can create and manage classes, distribute assignments, run mock "
            "exams, invite students by email, and monitor individual and class-wide "
            "performance.\n\n"
            "The backend is a Django REST Framework API secured with JWT, using "
            "PostgreSQL for storage and Celery + Redis for background tasks. The "
            "frontend is a modern Next.js / React app written in TypeScript and styled "
            "with Tailwind CSS, with the whole stack containerised using Docker."
        ),
        "extra_tech": ["Django", "Django REST Framework", "PostgreSQL", "Celery",
                       "Redis", "Next.js", "React", "Tailwind CSS", "Docker", "JWT"],
        "is_featured": True,
    },
    "volunteers_bot": {
        "title": "Volunteers Telegram Bot",
        "short_description": (
            "A production-ready Telegram bot for volunteer management — registration, "
            "FAQ, support tickets, and broadcasts."
        ),
        "long_description": (
            "Volunteers Bot is a production-oriented Telegram bot for managing "
            "volunteers, built with Python and aiogram 3. It handles registration "
            "through a guided FSM flow, a database-backed FAQ that admins can edit, and "
            "a support-ticket system where user messages reach an admin group and "
            "admins reply simply by responding to the bot's post.\n\n"
            "It also supports mass broadcasts (text or photo with optional URL buttons), "
            "a suggestions box, group commands, and a super-admin panel for searching "
            "users and promoting or demoting admins. The bot ships with Uzbek and "
            "Russian interfaces, per-user rate limiting, centralised logging, and a "
            "global error handler.\n\n"
            "It uses SQLAlchemy 2 (async) with PostgreSQL in production and SQLite "
            "locally, Redis for FSM state and rate limits, and Alembic for migrations."
        ),
        "extra_tech": ["aiogram", "SQLAlchemy", "PostgreSQL", "Redis", "Alembic"],
        "is_featured": True,
    },
    "iqtisodchi-bolajon-android-app": {
        "title": "Pul Olami — Kids' Finance Game",
        "short_description": (
            "A Flutter Android game that teaches financial literacy to schoolchildren "
            "(grades 1–4) in Uzbek."
        ),
        "long_description": (
            "Pul Olami (“World of Money”) is an Android game that introduces "
            "financial literacy to young children in grades 1–4, entirely in Uzbek. "
            "Kids learn through short lessons covering core money concepts, "
            "multiple-choice quizzes, a three-section shop with unlockable items, and a "
            "money-counting mini-game.\n\n"
            "The app is built with Flutter and Dart using a Material 3 theme, with a "
            "ChangeNotifier-based central game state and local persistence via "
            "SharedPreferences. Animated buttons and money displays keep the experience "
            "playful and engaging for its young audience."
        ),
        "extra_tech": ["Flutter", "Material Design"],
        "is_featured": True,
    },
    "portfolio": {
        "title": "Portfolio Website",
        "short_description": (
            "This very site — a production-grade, CMS-like Django portfolio with a full "
            "admin and a Markdown blog."
        ),
        "long_description": (
            "This portfolio website is a production-grade Django application with a "
            "dynamic, CMS-like structure — every section (hero, about, skills, "
            "experience, services, projects and blog) is editable from the Django admin "
            "without touching code.\n\n"
            "It features SEO optimisation with meta tags, Open Graph, a sitemap and RSS "
            "feed, a database-backed contact form, media management, and a "
            "Markdown-powered blog with syntax highlighting. It's deployed with Gunicorn "
            "and Nginx behind HTTPS — and it's the site you're looking at right now."
        ),
        "extra_tech": ["Django", "Gunicorn", "Nginx", "WhiteNoise"],
        "is_featured": True,
    },
    "movie_project": {
        "title": "Movie Platform",
        "short_description": (
            "A full-stack movie platform with a Django REST API and a classic Django "
            "web interface."
        ),
        "long_description": (
            "Movie Platform is a full-stack application built with Django and Django "
            "REST Framework. It exposes a RESTful API with CRUD operations for movies, "
            "JWT authentication, categories and genres, and pagination and filtering — "
            "alongside a classic Django web interface with movie list and detail pages "
            "and an admin panel for managing content.\n\n"
            "The project follows a clean, scalable architecture that separates the API "
            "app from the web app, backed by PostgreSQL."
        ),
        "extra_tech": ["Django", "Django REST Framework", "PostgreSQL", "JWT"],
        "is_featured": False,
    },
    "DarsPro": {
        "title": "DarsPro",
        "short_description": (
            "An online education platform with a Python backend and a TypeScript "
            "frontend, containerised with Docker."
        ),
        "long_description": (
            "DarsPro is an online learning platform that pairs a Python backend with a "
            "modern TypeScript frontend. It is built to deliver structured lessons and "
            "educational content through a fast, clean web interface, and is "
            "containerised with Docker for consistent deployment across environments."
        ),
        "extra_tech": ["Django", "Docker"],
        "is_featured": False,
    },
    "DSAT-mock-exam": {
        "title": "Digital SAT Mock Exam",
        "short_description": (
            "A Digital SAT mock-exam web app with a Python backend and a TypeScript "
            "frontend."
        ),
        "long_description": (
            "Digital SAT Mock Exam is a web application for taking full-length, "
            "Bluebook-style Digital SAT practice tests. It combines a Python backend "
            "with a TypeScript frontend to deliver a smooth, timed exam experience with "
            "scoring and review built in — a focused, standalone companion to the larger "
            "SAT learning platform."
        ),
        "extra_tech": ["Django"],
        "is_featured": False,
    },
    "shop": {
        "title": "Django Shop",
        "short_description": (
            "A Django e-commerce application with product catalog and media management."
        ),
        "long_description": (
            "Django Shop is a base e-commerce application built with Django. It provides "
            "product-catalog management through a dedicated products app, image and "
            "media handling, and a storefront ready to extend with cart and checkout "
            "features. It uses SQLite for development and Django's static/media handling, "
            "with the frontend built in HTML, CSS/SCSS and JavaScript."
        ),
        "extra_tech": ["Django"],
        "is_featured": False,
    },
    "HabitTracker": {
        "title": "Habit Tracker",
        "short_description": (
            "A Django web app for tracking daily habits and visualising progress."
        ),
        "long_description": (
            "Habit Tracker is a Django web application for building and maintaining "
            "daily habits. Users record habits each day and review their consistency "
            "over time through simple analytics, helping turn small daily actions into "
            "lasting routines."
        ),
        "extra_tech": ["Django"],
        "is_featured": False,
    },
    "weather-tracker": {
        "title": "Weather Tracker",
        "short_description": (
            "A Python application for fetching and tracking current weather conditions."
        ),
        "long_description": (
            "Weather Tracker is a Python application that retrieves and displays current "
            "weather data for a given location. It's a compact project demonstrating "
            "external API consumption and clean handling of third-party data in Python."
        ),
        "extra_tech": [],
        "is_featured": False,
    },
    "BMI-calculator": {
        "title": "BMI Calculator",
        "short_description": (
            "A simple Python program that calculates Body Mass Index from weight and "
            "height."
        ),
        "long_description": (
            "BMI Calculator is a small Python command-line program that calculates a "
            "user's Body Mass Index from their weight (in kilograms) and height (in "
            "meters). After computing the value it reports the BMI along with a short "
            "interpretation — underweight, normal, overweight, or obese — using only "
            "the Python standard library."
        ),
        "extra_tech": [],
        "is_featured": False,
    },
    "Datacode-Academy": {
        "title": "Datacode Academy",
        "short_description": (
            "An IT education platform built with Python for teaching and sharing "
            "programming knowledge."
        ),
        "long_description": (
            "Datacode Academy is an IT education platform built with Python, designed to "
            "teach programming and share knowledge about software and technology. It "
            "provides a structured way to deliver lessons and learning material to "
            "students interested in IT."
        ),
        "extra_tech": ["Django"],
        "is_featured": False,
    },
}

# Per-repo languages (from the GitHub languages API) used as a fallback when the
# live API is unavailable / rate-limited. Order roughly by bytes (most first).
LANGUAGES = {
    "LMS_SATFergana": ["TypeScript", "Python", "HTML", "JavaScript", "CSS", "Shell", "Dockerfile"],
    "volunteers_bot": ["Python", "Mako"],
    "iqtisodchi-bolajon-android-app": ["Dart", "Java", "Kotlin"],
    "portfolio": ["CSS", "HTML", "Python", "JavaScript"],
    "movie_project": ["Python", "HTML"],
    "DarsPro": ["TypeScript", "Python", "CSS", "Dockerfile", "JavaScript"],
    "DSAT-mock-exam": ["TypeScript", "Python", "Shell", "CSS", "JavaScript", "HTML"],
    "shop": ["HTML", "CSS", "SCSS", "JavaScript", "Python", "PHP"],
    "HabitTracker": ["Python"],
    "weather-tracker": ["Python"],
    "BMI-calculator": ["Python"],
    "Datacode-Academy": ["Python"],
}

# Repos to ignore entirely (profile README repo).
SKIP_REPOS = {"A1isherDev"}

# ── Experience (drafted; editable in admin) ────────────────────────────────────
# start/end are ISO date strings; end=None means current.
EXPERIENCE = [
    {
        "company": "Najot Ta'lim",
        "role": "Backend Development Student",
        "description": (
            "Studying backend development with a focus on Python, Django and Django "
            "REST Framework. Building real-world projects — REST APIs, Telegram bots "
            "and full-stack platforms — while learning clean architecture and best "
            "practices."
        ),
        "start": "2024-09-01",
        "end": None,
        "is_current": True,
        "order": 1,
    },
    {
        "company": "Freelance / Personal Projects",
        "role": "Backend Developer",
        "description": (
            "Designing and building backend systems and bots end to end — including a "
            "volunteer-management Telegram bot, a Digital SAT learning platform, and "
            "several Django web applications — covering database design, REST APIs, and "
            "deployment with Docker, Gunicorn and Nginx."
        ),
        "start": "2024-01-01",
        "end": None,
        "is_current": True,
        "order": 2,
    },
]

# ── Services (drafted from real work; editable) ────────────────────────────────
SERVICES = [
    {
        "title": "Backend Development",
        "description": "Robust, scalable server-side systems built with Python and Django.",
        "icon_class": "fas fa-server",
        "order": 1,
        "features": ["Django & DRF", "Database design", "Clean architecture"],
    },
    {
        "title": "REST API Development",
        "description": "Well-documented, secure REST APIs with authentication and clear contracts.",
        "icon_class": "fas fa-network-wired",
        "order": 2,
        "features": ["JWT authentication", "Pagination & filtering", "API documentation"],
    },
    {
        "title": "Telegram Bot Development",
        "description": "Production-ready Telegram bots with admin panels, broadcasts and multi-language support.",
        "icon_class": "fab fa-telegram",
        "order": 3,
        "features": ["aiogram 3", "FSM flows", "Admin tooling"],
    },
    {
        "title": "Deployment & DevOps",
        "description": "Containerised deployments and server setup for reliable, repeatable releases.",
        "icon_class": "fas fa-cloud",
        "order": 4,
        "features": ["Docker", "Nginx + Gunicorn", "SSL & domains"],
    },
]

# ── Blog (short drafted posts; Markdown is supported by the blog) ───────────────
ARTICLES = [
    {
        "title": "Building a Production-Ready Telegram Bot with aiogram 3",
        "slug": "production-ready-telegram-bot-aiogram-3",
        "category": "Backend Development",
        "tags": ["python", "telegram", "async"],
        "excerpt": (
            "Lessons from building a volunteer-management bot with aiogram 3, "
            "SQLAlchemy and Redis — FSM flows, support tickets and broadcasts."
        ),
        "content": (
            "Telegram bots are a great way to ship real value fast, but a *production* "
            "bot needs more than a few command handlers. While building my "
            "**Volunteers Bot**, I leaned on a few ideas that kept it maintainable.\n\n"
            "## Structure by responsibility\n\n"
            "Splitting the code into `handlers/`, `services/`, `database/` and "
            "`middlewares/` made each part easy to reason about. Routers group related "
            "handlers; business logic lives in services, not in the handlers.\n\n"
            "## State with FSM + Redis\n\n"
            "Multi-step flows like registration are perfect for aiogram's FSM. Backing "
            "the state with Redis means it survives restarts and scales beyond one "
            "process.\n\n"
            "## Treat admins as users too\n\n"
            "The support-ticket system simply forwards user messages to an admin group; "
            "admins reply by responding to the bot's post. No custom dashboard needed.\n\n"
            "Add rate limiting, centralised logging and a global error handler, and you "
            "have a bot that's ready for real traffic."
        ),
    },
    {
        "title": "Why I Chose Django REST Framework for My SAT Platform",
        "slug": "why-django-rest-framework-sat-platform",
        "category": "Backend Development",
        "tags": ["django", "api", "python"],
        "excerpt": (
            "Building an API-first SAT learning platform with Django REST Framework, "
            "PostgreSQL and a Next.js frontend."
        ),
        "content": (
            "When I started my **SAT LMS** platform, I went API-first: a Django REST "
            "Framework backend with a separate Next.js frontend. Here's why DRF was the "
            "right call.\n\n"
            "## Serializers do the heavy lifting\n\n"
            "Validation, representation and deserialization live in one place. Combined "
            "with viewsets and routers, a full CRUD resource takes very little code.\n\n"
            "## Auth that just works\n\n"
            "JWT authentication plugs straight in, which made it simple to share the "
            "same API between the web app and future mobile clients.\n\n"
            "## Room to grow\n\n"
            "Pagination, filtering and throttling are built in, and Celery + Redis "
            "handle the heavier background work like analytics. PostgreSQL ties it all "
            "together. The result is a clean, scalable backend I can keep extending."
        ),
    },
]

# ── SEO ────────────────────────────────────────────────────────────────────────
SEO_DATA = [
    {
        "page_key": "home",
        "meta_title": "Alisher Muhammadaliyev — Backend Developer",
        "meta_description": (
            "Portfolio of Alisher Muhammadaliyev, a backend developer from Uzbekistan "
            "building APIs, Telegram bots and web platforms with Python and Django."
        ),
        "meta_keywords": "Alisher Muhammadaliyev, backend developer, Python, Django, REST API, Uzbekistan, portfolio",
    },
    {
        "page_key": "pages/about",
        "meta_title": "About — Alisher Muhammadaliyev",
        "meta_description": (
            "Learn about Alisher Muhammadaliyev's background, skills and experience as "
            "a backend developer from Fergana, Uzbekistan."
        ),
        "meta_keywords": "about, backend developer, Django, Python, Najot Talim",
    },
]
