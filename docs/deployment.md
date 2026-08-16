[Back to README](../README.md)

# Deployment

For production deployment:

1. Change `SECRET_KEY` to a secure random value
2. Update `ADMIN_PASSWORD` to a strong password
3. Set `BACKEND_CORS_ORIGINS` to your frontend domain
4. Use a production database (PostgreSQL recommended)
5. Set `GOOGLE_CLIENT_ID` if using Google Sign-In