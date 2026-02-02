JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Al Barakah Admin",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Al Barakah Mart",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Al Barakah Admin",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "images/logo.png",

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": "images/logo.png",

    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": "images/logo.png",

    # Welcome text on the login screen
    "welcome_sign": "Welcome back to Al Barakah Admin",

    # Copyright on the footer
    "copyright": "Al Barakah Mart Ltd",

    # List of model admins to search from the search bar, search bar omitted if excluded
    # If you want to use a single search field you dont need to use a list, you can simply write "search_model": "auth.User"
    "search_model": ["users.User", "products.Product", "orders.Order"],

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": "image",

    ############
    # Top Menu #
    ############

    # Links to put along the top menu
    "topmenu_links": [

        # Url that gets reversed (Permissions can be added)
        {"name": "Dashboard",  "url": "admin:index", "permissions": ["auth.view_user"]},

        # external url that opens in a new window (Permissions can be added)
        {"name": "View Site", "url": "/", "new_window": True},

        # model admin to link to (Permissions checked against model)
        {"model": "users.User"},

        # App with dropdown menu to all its models pages (Permissions checked against models)
        {"app": "products"},
    ],

    #############
    # User Menu #
    #############

    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "users.User"}
    ],

    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        "analytics": [{
            "name": "Dashboard", 
            "url": "analytics_dashboard", 
            "icon": "fas fa-chart-line",
            "permissions": ["analytics.view_visitorsession"]
        }]
    },

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": [
        "orders",
        "orders.Order",
        "orders.OrderStatusHistory",
        "orders.PaymentGateway",
        "products",
        "products.Product",
        "products.Category",
        "products.Brand",
        "products.Review",
        "products.StockLog",
        "products.Wishlist",
        "users",
        "users.User",
        "users.Address",
        "users.SupportTicket",
        "users.Wallet",
        "marketing",
        "marketing.Coupon",
        "marketing.DealOfTheDay",
        "marketing.HomeSlider",
        "core",
        "core.ChatbotSettings",
        "core.ChatbotFAQ",
        "core.ChatbotSuggestion",
        "core.ChatbotIntent",
        "core.ContactMessage",
        "core.SiteSettings",
        "account",
        "analytics",
        "auth",
        "sites",
        "socialaccount"
    ],

    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user",
        "users.Address": "fas fa-map-marker-alt",
        "users.Wallet": "fas fa-wallet",
        "users.SupportTicket": "fas fa-headset",
        "products.Product": "fas fa-box",
        "products.Category": "fas fa-tags",
        "products.Brand": "fas fa-copyright",
        "products.Review": "fas fa-star",
        "products.Wishlist": "fas fa-heart",
        "products.StockLog": "fas fa-clipboard-list",
        "orders.Order": "fas fa-shopping-cart",
        "orders.OrderItem": "fas fa-list",
        "orders.Courier": "fas fa-truck",
        "orders.OrderStatusHistory": "fas fa-history",
        "orders.PaymentGateway": "fas fa-credit-card",
        "marketing.HomeSlider": "fas fa-images",
        "marketing.Coupon": "fas fa-ticket-alt",
        "marketing.DealOfTheDay": "fas fa-clock",
        "core.SiteSettings": "fas fa-cogs",
        "core.ContactMessage": "fas fa-envelope",
        "core.ChatbotFAQ": "fas fa-question-circle",
        "core.ChatbotSettings": "fas fa-robot",
        "core.ChatbotSuggestion": "fas fa-lightbulb",
        "core.ChatbotIntent": "fas fa-bullseye",
        "account.EmailAddress": "fas fa-at",
        "analytics.AnalyticsEvent": "fas fa-chart-bar",
        "analytics.PageView": "fas fa-eye",
        "analytics.VisitorSession": "fas fa-user-clock",
        "sites.Site": "fas fa-globe",
        "socialaccount.SocialAccount": "fas fa-share-alt",
        "socialaccount.SocialToken": "fas fa-key",
        "socialaccount.SocialApp": "fas fa-mobile-alt",
    },
    # Icons that are used when one is not specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": "css/custom_admin.css",
    "custom_js": None,
    # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    # Add a language dropdown into the admin
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-success",
    "sidebar_nav_child_indent": False,
    "sidebar_compact": False,
    "sidebar_child_indent": False,
    "sidebar_disable_expand": False,
    "brand_logo": None,
    "logo_small": None,
}
