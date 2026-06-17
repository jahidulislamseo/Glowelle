# GlowElle BD — Website Log
**Last Updated:** 2026-06-17  
**Project Type:** Django E-Commerce Platform  
**Business:** অর্গানিক গ্রোসারি ও দৈনন্দিন পণ্য — Dhaka, Bangladesh

---

## প্রজেক্ট ওভারভিউ

| বিষয় | তথ্য |
|-------|------|
| Framework | Django 5.1+ |
| Database | SQLite (dev) / PostgreSQL (production) |
| Frontend | Tailwind CSS + Lucide Icons |
| Image Storage | Cloudinary (production) / Local (dev) |
| Admin UI | Jazzmin |
| Authentication | Email-based + Google/Facebook OAuth + OTP |
| Hosting | Render / Vercel compatible |

---

## Apps এবং Models

### 1. `core` — সাইটের মূল সেটিং

| Model | কাজ |
|-------|-----|
| `SiteSettings` | সাইটের নাম, লোগো, ফোন, ইমেইল, সোশ্যাল লিংক, GA4 ট্র্যাকিং |
| `ContactMessage` | কনটাক্ট ফর্ম থেকে আসা মেসেজ |

---

### 2. `users` — ইউজার ম্যানেজমেন্ট

| Model | কাজ |
|-------|-----|
| `User` | কাস্টম ইউজার মডেল — email-based লগইন, phone, role |
| `Address` | একাধিক ডেলিভারি ঠিকানা, default ঠিকানা সাপোর্ট |
| `Wallet` | ডিজিটাল ওয়ালেট — ব্যালেন্স ও loyalty points |
| `WalletTransaction` | ওয়ালেট লেনদেনের ইতিহাস |
| `SupportTicket` | কাস্টমার সাপোর্ট টিকেট — open/in_progress/closed |

---

### 3. `products` — পণ্য ম্যানেজমেন্ট

| Model | কাজ |
|-------|-----|
| `Category` | পণ্যের ক্যাটাগরি — SEO metadata সহ |
| `Brand` | ব্র্যান্ড ম্যানেজমেন্ট |
| `Product` | মূল পণ্য — দাম, স্টক, ইমেজ, SEO, রেটিং |
| `ProductVariant` | সাইজ/কালার ভ্যারিয়েন্ট — আলাদা স্টক ও দাম |
| `ProductImage` | একটি পণ্যের একাধিক ছবি |
| `ProductVideo` | পণ্যের ভিডিও |
| `StockLog` | স্টক পরিবর্তনের অডিট ট্রেইল |
| `Review` | ইউজার রিভিউ ও রেটিং (১-৫ তারা) |
| `StockAlert` | স্টক আসলে ইউজারকে নোটিফিকেশন |
| `Wishlist` | ইউজারের উইশলিস্ট |

**বিশেষ ফিচার:**
- ইমেজ সেভ হলে স্বয়ংক্রিয় WebP কনভার্সন ও 1024×1024 রিসাইজ
- স্টক রেস কন্ডিশন এড়াতে Django F() expressions ব্যবহার

---

### 4. `orders` — অর্ডার ম্যানেজমেন্ট

| Model | কাজ |
|-------|-----|
| `Order` | সম্পূর্ণ অর্ডার — রেফারেন্স, স্ট্যাটাস, পেমেন্ট, ডেলিভারি |
| `OrderItem` | অর্ডারের প্রতিটি পণ্য আইটেম |
| `OrderStatusHistory` | অর্ডার স্ট্যাটাস পরিবর্তনের ইতিহাস |
| `Courier` | ডেলিভারি কুরিয়ার — ট্র্যাকিং URL সহ |
| `PaymentGateway` | পেমেন্ট গেটওয়ে — bKash, Nagad ইত্যাদি |

**অর্ডার স্ট্যাটাস ফ্লো:**
```
pending → processing → shipped → delivered
                              ↘ cancelled / returned
```

**বিশেষ ফিচার:**
- অর্ডার ক্যান্সেল/রিটার্নে স্বয়ংক্রিয় স্টক ফেরত
- অনলাইন পেমেন্ট রিফান্ড সরাসরি ওয়ালেটে
- PDF ইনভয়েস জেনারেশন
- স্ট্যাটাস বদলালে ইমেইল নোটিফিকেশন

---

### 5. `analytics` — ভিজিটর ও ইভেন্ট ট্র্যাকিং

| Model | কাজ |
|-------|-----|
| `VisitorSession` | সেশন-লেভেল ট্র্যাকিং — ডিভাইস, ব্রাউজার, লোকেশন |
| `PageView` | প্রতিটি পেজ ভিজিটের রেকর্ড |
| `AnalyticsEvent` | সার্চ, কার্টে যোগ, চেকআউট, পেমেন্ট ইভেন্ট |

**ট্র্যাক করা ইভেন্ট:**
`search`, `add_to_cart`, `remove_from_cart`, `checkout_start`, `payment_success`, `payment_failed`, `login`, `signup`, `logout`, `404`, `out_of_stock_click`, `wishlist_add`, `coupon_used`

---

### 6. `chatbot` — AI চ্যাটবট

| Model | কাজ |
|-------|-----|
| `ChatbotSettings` | ওয়েলকাম মেসেজ, সিস্টেম প্রম্পট, কাজের সময় |
| `ChatbotFAQ` | প্রশ্ন-উত্তর জোড়া — keyword trigger সহ |
| `ChatbotSuggestion` | Quick reply বাটন |
| `ChatbotIntent` | ইন্টেন্ট ক্লাসিফিকেশন — buying/support/discount ইত্যাদি |
| `ChatbotConversationMemory` | সেশন-ভিত্তিক কথোপকথনের ইতিহাস |
| `ChatbotAnalytics` | দৈনিক কনভার্সেশন সামারি |
| `ChatbotMetric` | প্রতি সেশনের মেট্রিক্স |
| `PopularProduct` | চ্যাটবটে জিজ্ঞাসিত জনপ্রিয় পণ্য |

**কাজের সময়:** ৯ AM – ১০ PM (বাইরে অটো অফলাইন মেসেজ)

---

### 7. `marketing` — মার্কেটিং টুলস

| Model | কাজ |
|-------|-----|
| `Coupon` | ডিসকাউন্ট কোড — মেয়াদ ও শতাংশ ভিত্তিক |
| `HomeSlider` | হোমপেজ ক্যারোসেল ব্যানার |
| `DealOfTheDay` | ফিচার্ড ডিল — কাউন্টডাউন সহ |
| `SellingNote` | ট্রাস্ট ব্যাজ — "ফ্রি ডেলিভারি", "১০০% ফ্রেশ" ইত্যাদি |

---

## URL স্ট্রাকচার

### Public Pages
| URL | পেজ |
|-----|-----|
| `/` | হোমপেজ |
| `/shop/` | সব পণ্য |
| `/product/<slug>/` | পণ্যের বিস্তারিত |
| `/about/` | আমাদের সম্পর্কে |
| `/contact/` | যোগাযোগ |
| `/faq/` | সাধারণ প্রশ্ন |
| `/privacy/` | প্রাইভেসি পলিসি |
| `/terms/` | শর্তাবলী |
| `/sitemap.xml` | XML সাইটম্যাপ |
| `/robots.txt` | রোবটস ফাইল |

### Authentication
| URL | কাজ |
|-----|-----|
| `/register/` | নিবন্ধন |
| `/login/` | লগইন |
| `/logout/` | লগআউট |
| `/otp/request/` | OTP পাঠানো |
| `/otp/verify/` | OTP যাচাই |
| `/accounts/` | Google/Facebook OAuth |

### User Dashboard
| URL | কাজ |
|-----|-----|
| `/dashboard/` | ইউজার ড্যাশবোর্ড |
| `/dashboard/orders/` | অর্ডার ইতিহাস |
| `/dashboard/addresses/` | ঠিকানা ম্যানেজমেন্ট |
| `/dashboard/wallet/` | ওয়ালেট |
| `/dashboard/support/` | সাপোর্ট টিকেট |
| `/profile/` | প্রোফাইল এডিট |

### Shopping
| URL | কাজ |
|-----|-----|
| `/cart/` | শপিং কার্ট |
| `/cart/add/<id>/` | কার্টে যোগ করা (AJAX) |
| `/cart/remove/<id>/` | কার্ট থেকে সরানো |
| `/checkout/` | চেকআউট |
| `/payment/<order_id>/` | পেমেন্ট |
| `/coupon/apply/` | কুপন কোড ব্যবহার |
| `/wishlist/` | উইশলিস্ট |

### Admin
| URL | কাজ |
|-----|-----|
| `/admin/` | অ্যাডমিন ড্যাশবোর্ড |
| `/admin/analytics/` | অ্যানালিটিক্স ড্যাশবোর্ড |
| `/admin/orders/invoice/<id>/` | PDF ইনভয়েস |
| `/admin/dashboard/stats/` | Stats API |

### APIs
| URL | কাজ |
|-----|-----|
| `/api/products/` | পণ্য REST API |
| `/api/categories/` | ক্যাটাগরি REST API |
| `/api/chatbot/` | চ্যাটবট API |
| `/api/get-history/` | চ্যাট ইতিহাস API |

---

## Templates স্ট্রাকচার

```
templates/
├── admin/                    # কাস্টম অ্যাডমিন টেমপ্লেট
│   ├── index.html            # অ্যাডমিন হোম ড্যাশবোর্ড
│   ├── analytics_dashboard.html
│   ├── change_form.html      # অর্ডার/পণ্য কাস্টম ফর্ম
│   ├── search_form.html
│   └── filter.html
│
├── emails/                   # ইমেইল টেমপ্লেট (১২+)
│   ├── order_confirmation.html
│   ├── order_status_update.html
│   ├── return_refund_update.html
│   ├── stock_alert.html
│   ├── otp_verification.html
│   ├── welcome.html
│   ├── wallet_credit.html
│   ├── support_ticket_created.html
│   ├── admin_new_order.html
│   ├── admin_low_stock.html
│   ├── admin_new_ticket.html
│   └── admin_contact_message.html
│
├── pages/                    # স্ট্যাটিক পেজ
│   ├── about.html
│   ├── contact.html
│   ├── faq.html
│   ├── privacy.html
│   └── terms.html
│
├── chatbot/
│   ├── admin/chat_history.html
│   └── chatbot_test.html
│
├── base.html
├── 404.html
└── 500.html

products/templates/products/
├── home.html                 # হোমপেজ
├── shop.html                 # পণ্য লিস্টিং
├── product_detail.html       # পণ্যের বিস্তারিত
├── wishlist.html
└── partials/
    ├── product_card.html
    ├── product_list.html
    ├── quick_view_content.html
    └── search_suggestions.html

orders/templates/orders/
├── cart_detail.html
├── create.html               # চেকআউট
├── created.html              # অর্ডার সম্পন্ন
├── order_detail.html
├── payment.html
└── admin/invoice_pdf.html
```

---

## Email নোটিফিকেশন সিস্টেম

| ট্রিগার | রিসিভার |
|---------|---------|
| নতুন অর্ডার | ইউজার + অ্যাডমিন |
| অর্ডার স্ট্যাটাস পরিবর্তন | ইউজার |
| রিটার্ন/রিফান্ড আপডেট | ইউজার |
| স্টক এলার্ট (পণ্য ফিরে এলে) | ইউজার |
| OTP কোড | ইউজার |
| ওয়েলকাম মেসেজ | নতুন ইউজার |
| ওয়ালেট ক্রেডিট | ইউজার |
| সাপোর্ট টিকেট তৈরি | ইউজার + অ্যাডমিন |
| লো স্টক এলার্ট | অ্যাডমিন |
| নতুন কনটাক্ট মেসেজ | অ্যাডমিন |

---

## পেমেন্ট সিস্টেম

| মেথড | বিবরণ |
|------|-------|
| Cash on Delivery (COD) | ডেলিভারিতে নগদ পেমেন্ট |
| Online Payment | bKash, Nagad, ইত্যাদি |

**পেমেন্ট স্ট্যাটাস:** `unpaid` → `paid` / `partial` / `refunded`

---

## Static ও Media ফাইল

| ধরন | লোকেশন |
|-----|---------|
| Static files | `theme/static/` — WhiteNoise দিয়ে সার্ভ |
| Custom CSS | `theme/static/css/custom_admin.css` |
| Media (dev) | `/media/` — লোকাল |
| Media (prod) | Cloudinary |

---

## Security কনফিগারেশন (Production)

- HTTPS বাধ্যতামূলক (SSL Redirect)
- Secure cookies (Session + CSRF)
- HSTS: ১ বছর (subdomains + preload সহ)
- X-Frame-Options: DENY (clickjacking প্রতিরোধ)
- XSS Filter সক্রিয়
- Content-Type Sniffing বন্ধ

---

## তৃতীয় পক্ষের লাইব্রেরি

| লাইব্রেরি | কাজ |
|-----------|-----|
| `jazzmin` | সুন্দর অ্যাডমিন UI |
| `django-allauth` | Google/Facebook OAuth |
| `django-import-export` | Excel ইম্পোর্ট/এক্সপোর্ট |
| `cloudinary` | ক্লাউড ইমেজ স্টোরেজ |
| `whitenoise` | Static ফাইল সার্ভিং |
| `rest_framework` | REST API |
| `corsheaders` | CORS হেডার |
| `django-markdownify` | Markdown → HTML |
| `Pillow` | ইমেজ প্রসেসিং |
| `python-decouple` | Environment variables |
| `dj-database-url` | Database URL পার্সিং |

---

## প্রজেক্ট পরিসংখ্যান

| মেট্রিক | সংখ্যা |
|---------|--------|
| Django Apps | ৭ |
| Database Models | ৪০+ |
| URL Patterns | ৫০+ |
| HTML Templates | ৫২+ |
| Email Templates | ১২+ |
| Database Indexes | ১৫+ |

---

## লোকাল ডেভেলপমেন্ট কমান্ড

```bash
# Server চালু করা
.\run.bat

# অথবা ম্যানুয়ালি
venv\Scripts\activate
python manage.py runserver

# Migration চালানো
python manage.py makemigrations
python manage.py migrate

# Superuser তৈরি
python manage.py createsuperuser

# Static files কালেক্ট (production)
python manage.py collectstatic
```

**Server URL:** http://127.0.0.1:8000  
**Admin URL:** http://127.0.0.1:8000/admin/
