"""
SSO JWT verification module.

Supports RS256 JWTs carrying a `jku` header that points to a JWKS endpoint.
The public key is fetched once and cached in-process by key-id (kid).
"""
import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from . import config

# In-process JWKS cache: kid -> public_key_object
_jwks_cache: dict = {}


def _validate_jku(jku: str) -> bool:
    """Ensure the JWKS endpoint originates from the trusted SSO provider."""
    return bool(config.SSO_JKU_VALIDATOR.match(jku))


def _fetch_public_key(jku: str, kid: str):
    """Fetch JWKS from *jku* and return the key matching *kid*, caching it."""
    if kid in _jwks_cache:
        return _jwks_cache[kid]

    resp = requests.get(jku, timeout=5, verify=False)
    resp.raise_for_status()
    jwks = resp.json()

    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            public_key = RSAAlgorithm.from_jwk(key_data)
            _jwks_cache[kid] = public_key
            return public_key

    raise ValueError(f"kid '{kid}' not found in JWKS at {jku}")


def verify_sso_token(token: str) -> dict:
    """
    Decode and verify a bearer SSO token.
    Returns the payload dict on success, raises on failure.
    """
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise ValueError(f"Malformed token header: {exc}") from exc

    jku = header.get("jku")
    kid = header.get("kid")

    if not jku or not kid:
        raise ValueError("Token must carry both 'jku' and 'kid' header claims")

    if not _validate_jku(jku):
        raise ValueError("Untrusted JWKS endpoint")

    public_key = _fetch_public_key(jku, kid)

    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_exp": True},
    )
    return payload
