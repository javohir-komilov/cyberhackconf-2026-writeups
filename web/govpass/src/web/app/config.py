import os
import re

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/govpass.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

FLAG = os.environ.get("FLAG", "CHC{fake_flag_for_testing}")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# Validates JWKS URL against trusted SSO domain
SSO_JKU_VALIDATOR = re.compile(r"^https?://sso\.govpass\.local")
