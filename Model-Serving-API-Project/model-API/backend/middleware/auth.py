import os
import requests
import json
from functools import lru_cache
from typing import Dict

from fastapi import Depends, HTTPException, Request
from fastapi.security import SecurityScopes
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError

# --- Environment Variables for Auth0 Integration ---
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")                     # Your Auth0 tenant domain
API_IDENTIFIER = os.getenv("API_IDENTIFIER")                 # Identifier for this API (audience)
ALGORITHMS = json.loads(os.getenv("ALGORITHMS", '["RS256"]'))             # JWT algorithm (default RS256)


# --- JWKS Fetching & Caching ---
@lru_cache()
def get_jwks():
    """
    Fetch the JSON Web Key Set (JWKS) from Auth0 and cache the result in memory.
    These keys are used to verify the signature of incoming JWTs.
    """
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    return requests.get(jwks_url).json()


# --- Custom HTTPBearer Class with JWT Verification ---
class Auth0JWTBearer(HTTPBearer):
    """
    Custom FastAPI security scheme that uses Auth0-issued Bearer tokens (JWTs).
    It validates the token against Auth0’s JWKS and returns the decoded payload.
    """
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Dict:
        """
        Extract and verify the Bearer token from the request Authorization header.
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(status_code=403, detail="Missing authorization credentials")

        token = credentials.credentials
        return self.verify_jwt(token)

    def verify_jwt(self, token: str) -> Dict:
        """
        Validate the JWT by verifying its signature and claims against Auth0's public JWKS.
        Returns the decoded payload if successful.
        """
        try:
            # Extract unverified header to get the key ID (kid)
            unverified_header = jwt.get_unverified_header(token)

            # Get JWKS and find the matching public key by 'kid'
            jwks = get_jwks()
            rsa_key = None
            for key in jwks["keys"]:
                if key["kid"] == unverified_header.get("kid"):
                    rsa_key = jwk.construct(key)
                    break

            if rsa_key is None:
                raise HTTPException(status_code=401, detail="Public key not found in JWKS")

            # Decode and verify the token's signature and claims
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_IDENTIFIER,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )

            return payload

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError as e:
            raise HTTPException(status_code=403, detail=f"Token validation failed: {str(e)}")


# --- Dependency to Enforce Scopes from JWT ---
def get_current_user_with_scopes(
    security_scopes: SecurityScopes,
    token_payload: Dict = Depends(Auth0JWTBearer())
) -> Dict:
    """
    Validates that the JWT payload includes all required scopes as defined in the route.

    This allows you to protect routes with:
        @Security(get_current_user_with_scopes, scopes=["scope:required"])
    """
    token_scopes = token_payload.get("scope", "").split()

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scope: {scope}"
            )

    return token_payload
