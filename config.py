import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pawshaven-flask-secret-2024-production')
    JWT_SECRET = 'pawshaven-jwt-hmac-sha256-secret-key-2024'
    JWT_ALGORITHM = 'HS256'
    
    # Secure Host Admin Hash (SHA-256)
    # To change: echo -n "yourpassword" | sha256sum
    HOST_ADMIN_HASH = os.environ.get('HOST_ADMIN_HASH', 'f43eab41b04613669cd92ba457c855055864d6d25c0488bbeb59e1d23c24f586')

    APP_PORT = 5000
    DEBUG = True

    # Sandbox base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SANDBOX_DIR = os.path.join(BASE_DIR, 'data', 'sandboxes')
    DOCUMENTS_DIR = os.path.join(BASE_DIR, 'documents')

    # Internal service ports (SSRF targets)
    VET_RECORDS_PORT = 8080
    BILLING_PORT = 9090
    METADATA_PORT = 1337

    # "Production" secrets 
    DATABASE_URI = 'postgresql://pawshaven_admin:V3t_Pr0d_P@ss!2024@pawshaven-db.c9ak27s.us-east-1.rds.amazonaws.com:5432/pawshaven_prod'
    AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'
    AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    STRIPE_SECRET = 'sk_live_paws_4eC39HqLyjWDarjtT1zdp7dc'
    SENDGRID_KEY = 'SG.pawshaven.xxxxxxxxx.yyyyyyyy'

    # Upload config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
