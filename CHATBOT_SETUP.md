# 🚀 Advanced Chatbot Features - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate

# Install new packages
pip install twilio deep-translator

# Or install all from requirements.txt
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
python manage.py makemigrations chatbot
python manage.py migrate
```

### 3. Configure Environment Variables

Copy the example file and add your credentials:

```bash
# Copy example file
copy .env.chatbot.example .env.chatbot

# Then add these to your main .env file:
```

**Required for Notifications:**

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890
SUPPORT_PHONE=+880 1609132361
```

**Required for Payments:**

```env
# bKash
BKASH_APP_KEY=your_key
BKASH_APP_SECRET=your_secret
BKASH_USERNAME=your_username
BKASH_PASSWORD=your_password

# Nagad
NAGAD_MERCHANT_ID=your_id

# SSL Commerz
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_password
SSLCOMMERZ_IS_SANDBOX=True
```

**Site Configuration:**

```env
SITE_URL=https://yoursite.com
```

### 4. Test the Features

```bash
# Run development server
python manage.py runserver

# Visit chatbot
http://localhost:8000/

# Visit admin dashboard
http://localhost:8000/admin/chatbot/
```

---

## Feature Testing Checklist

### ✅ Analytics Dashboard

1. Go to `/admin/chatbot/chatbotanalytics/`
2. Check if metrics are being tracked
3. Send a few chat messages
4. Verify session metrics update

### ✅ AI Recommendations

1. Login as a user with order history
2. Open chatbot
3. Ask: "Mach ase?"
4. Verify recommendations appear

### ✅ Notifications

1. Create a test order
2. Change order status in admin
3. Check if SMS/Email/WhatsApp sent
4. Verify notification content

### ✅ Multi-Language Support

1. Try Bengali: "মাছ আছে?"
2. Try English: "Do you have fish?"
3. Try Banglish: "Apnader fish ase?"
4. Verify bot responds in same language

### ✅ Payment Integration

1. Place an order via chatbot
2. Request payment link
3. Verify link generation
4. Test payment flow (sandbox)

### ✅ Smart Discounts

1. Login as new user
2. Check for first-time discount
3. Add items worth 1000+ BDT
4. Verify discount suggestions

### ✅ Order Management

1. Login with existing orders
2. Try: "Last order repeat koro"
3. Try: "Amar order history dekha"
4. Try: "Order cancel korbo"

### ✅ Personality

1. Test at different times of day
2. Check time-based greetings
3. Test on festival days
4. Verify contextual responses

---

## Troubleshooting

### Issue: Twilio not sending messages

**Solution:**

- Verify credentials in `.env`
- Check Twilio account balance
- Ensure phone numbers are verified (sandbox mode)

### Issue: Payment links not generating

**Solution:**

- Check payment gateway credentials
- Verify `SITE_URL` is set correctly
- Test with sandbox credentials first

### Issue: Recommendations not showing

**Solution:**

- Ensure user has order history
- Check if products exist in database
- Verify user is logged in

### Issue: Language detection not working

**Solution:**

- Install `deep-translator`: `pip install deep-translator`
- Check internet connection (for translation API)

---

## Production Deployment

### Before Going Live:

1. **Update Environment Variables:**

   ```env
   # Change to production URLs
   BKASH_BASE_URL=https://checkout.bkash.com
   SSLCOMMERZ_IS_SANDBOX=False
   SITE_URL=https://yourproductionsite.com
   ```

2. **Verify Twilio Account:**
   - Upgrade from trial account
   - Add billing information
   - Verify all phone numbers

3. **Test Payment Gateways:**
   - Get production credentials
   - Test with real transactions
   - Verify webhook URLs

4. **Security Checklist:**
   - [ ] All API keys in environment variables
   - [ ] HTTPS enabled
   - [ ] CSRF protection enabled
   - [ ] Rate limiting configured

5. **Performance:**
   - [ ] Database indexes created
   - [ ] Static files collected
   - [ ] Caching configured
   - [ ] CDN setup (optional)

---

## Monthly Cost Breakdown

| Service              | Free Tier        | Paid (Low Volume) | Paid (High Volume) |
| -------------------- | ---------------- | ----------------- | ------------------ |
| **Twilio SMS**       | $15 credit       | $10-30/month      | $50-100/month      |
| **Twilio WhatsApp**  | Trial            | $5-15/month       | $20-50/month       |
| **Google Translate** | 500K chars/month | $0-5/month        | $10-20/month       |
| **bKash**            | Free             | 1-1.5% fee        | 1% fee             |
| **SSL Commerz**      | Free             | 2-2.5% fee        | 1.5-2% fee         |
| **Total**            | **~$15**         | **$35-85/month**  | **$100-200/month** |

---

## Support & Documentation

- **Twilio Docs:** https://www.twilio.com/docs
- **bKash API:** https://developer.bkash.com/
- **SSL Commerz:** https://developer.sslcommerz.com/
- **Django Docs:** https://docs.djangoproject.com/

---

## Next Steps

1. ✅ Test all features locally
2. ✅ Configure production credentials
3. ✅ Deploy to staging environment
4. ✅ Run user acceptance testing
5. ✅ Deploy to production
6. ✅ Monitor analytics dashboard
7. ✅ Gather user feedback
8. ✅ Iterate and improve

**Your chatbot is now a fully-featured, intelligent assistant!** 🎉
