# ShareDocs - Document Sharing Platform

A secure document sharing platform built with Django that allows users to upload, manage, and share files with others.

## Live Demo

The application is live at: [https://sharedocs-bdh4.onrender.com/](https://sharedocs-bdh4.onrender.com/)

## Features

- User Authentication (Signup/Login)
- File Upload and Management
- Secure File Sharing
- Public/Private File Visibility
- Temporary Shareable Links
- File Comments and Collaboration
- Secure File Storage

## Tech Stack

- Backend: Django 4.2.21
- Database: PostgreSQL
- File Storage: AWS S3 (via django-storages)
- Web Server: Gunicorn
- Static Files: WhiteNoise

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8+
- PostgreSQL
- Node.js (for frontend assets)
- AWS S3 account (for file storage)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd ShareDocs
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/sharedocs
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

5. Run database migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Usage

1. Access the application at `http://localhost:8000`
2. Sign up for a new account or log in with existing credentials
3. Upload files through the web interface
4. Manage your files in the "My Files" section
5. Share files by:
   - Making them public
   - Generating temporary shareable links
   - Copying direct download URLs

## Security Features

- Secure password hashing using Django's built-in password hasher
- CSRF protection for all forms
- Secure file storage using AWS S3
- Token-based authentication
- Temporary URLs with expiration
- Protected file access control

## API Endpoints

The application provides RESTful API endpoints for:
- User authentication
- File management
- File sharing
- Comment management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django framework for backend development
- AWS S3 for scalable file storage
- Various open-source packages and dependencies

## Contact

For support or questions, please open an issue in the GitHub repository.