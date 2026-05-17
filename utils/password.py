"""
Password utilities: strength checking and hashing (bcrypt)
"""

import re
import bcrypt


# ---------------------------------------------------------------------------
# Password strength checker
# ---------------------------------------------------------------------------

def check_password_strength(password: str) -> dict:
    """
    Evaluate password strength across five criteria.

    Returns a dict with:
        score       : 0-5 (one point per criterion met)
        level       : 'Very Weak' | 'Weak' | 'Fair' | 'Strong' | 'Very Strong'
        criteria    : dict of individual criterion results (bool)
        suggestions : list of improvement hints
    """
    criteria = {
        "length":    len(password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "digit":     bool(re.search(r"\d", password)),
        "special":   bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", password)),
    }

    score = sum(criteria.values())

    levels = {0: "Very Weak", 1: "Very Weak", 2: "Weak", 3: "Fair", 4: "Strong", 5: "Very Strong"}
    level = levels[score]

    suggestions = []
    if not criteria["length"]:
        suggestions.append("Use at least 8 characters.")
    if not criteria["uppercase"]:
        suggestions.append("Add at least one uppercase letter (A-Z).")
    if not criteria["lowercase"]:
        suggestions.append("Add at least one lowercase letter (a-z).")
    if not criteria["digit"]:
        suggestions.append("Add at least one number (0-9).")
    if not criteria["special"]:
        suggestions.append("Add at least one special character (!@#$%^&* …).")

    return {
        "score": score,
        "level": level,
        "criteria": criteria,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Hashing helpers (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plain_text: str) -> str:
    """Hash a plain-text password with bcrypt (salt is embedded in the hash)."""
    return bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_text: str, hashed: str) -> bool:
    """Return True if plain_text matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed.encode("utf-8"))
