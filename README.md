# Grocerly E-Commerce Platform

![Grocerly Logo](https://grocerly-ecom.onrender.com/static/assets/imgs/theme/logo.png)

Grocerly is a fully functional, multi-vendor e-commerce web application designed to provide a seamless shopping experience. Built with Python and Django, this platform supports dynamic product management, user authentication, a comprehensive shopping cart system, secure vendor dashboards, and an AI-powered shopping assistant.

## 🌐 Live Demo
**Check out the live deployment here:** [https://grocerly-ecom.onrender.com](https://grocerly-ecom.onrender.com/)

*(Note: Since this is hosted on a free Render instance, it might take a minute to spin up upon initial request).*

## 🚀 Key Features

*   **AI Shopping Assistant**: Integrated with Google's Gemini AI to provide a smart chat widget that helps customers search for products, answer queries, and manage their cart.
*   **VNPay Payment Gateway**: Secure online checkout process with VNPay integration for fast and reliable payments.
*   **Dynamic AJAX Filtering**: Real-time product filtering by categories, tags, vendors, and price slider without reloading the page.
*   **Multilingual Support (i18n)**: Fully supports English and Vietnamese, with smart middleware ensuring the preferred default language.
*   **Multi-Vendor System**: Vendors can register, upload products, manage inventory, and track their sales via a dedicated dashboard.
*   **Dynamic Shopping Cart**: Real-time cart updates, session-based cart management, coupon application, and a seamless checkout process.
*   **Robust Data Safety**: Implements soft-deletion for critical models (like Products) to prevent accidental data loss.
*   **User Profiles & Authentication**: Secure sign-up/login, wishlists, address management, and order history tracking.
*   **Product Reviews & Ratings**: Customers can leave feedback and ratings on products they've purchased.
*   **Cloud Media Storage**: All product images and user uploads are securely stored and delivered via Cloudinary.
*   **Modern Admin Panel**: Powered by `django-jazzmin` for an intuitive and beautiful admin interface.

## 🛠️ Technology Stack

*   **Backend framework:** Django 5.2 (Python 3)
*   **AI Integration:** Google Generative AI SDK (Gemini)
*   **Database:** PostgreSQL (Hosted on Neon.tech)
*   **Media Storage:** Cloudinary & WhiteNoise (for static assets)
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript, Bootstrap, jQuery (for AJAX)
*   **Hosting/Deployment:** Render

## ⚙️ Local Development Setup

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/leducphat/grocerly-ecom.git
    cd grocerly-ecom
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    cd grocerly
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to `.env` and fill in your local Postgres database credentials and Cloudinary API keys.

5.  **Run migrations and start the server:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

## 📝 License
This project is open-source and available under the MIT License.
