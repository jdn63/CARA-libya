from app import app

if __name__ == "__main__":
    import os
    import warnings
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    if debug:
        warnings.warn(
            "Flask debug mode is ENABLED (FLASK_DEBUG=1). "
            "This exposes the interactive debugger — never set this in production. "
            "The production server (gunicorn) ignores this flag entirely.",
            stacklevel=1,
        )
    app.run(host="0.0.0.0", port=5000, debug=debug)
