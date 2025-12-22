
# Unfold Admin Settings
UNFOLD = {
    "SITE_TITLE": "Al Barakah Mart Admin",
    "SITE_HEADER": "Al Barakah Mart",
    "SITE_URL": "/",
    "DASHBOARD_CALLBACK": "users.views.dashboard_callback", # Optional: for custom dashboard widgets
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Navigation",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": "admin:index",
                    },
                ],
            },
        ],
    },
}
