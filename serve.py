import argparse
import os

# 1. Usanidi wa Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="Port kwa ajili ya debug server", default=4000, type=int)
parser.add_argument(
    "--profile", help="Washa flask_profiler kuona utendaji (performance)", action="store_true"
)
parser.add_argument(
    "--disable-gevent",
    help="Zima gevent na monkey patching",
    action="store_true", # Imebadilishwa kuwa true ili kulingana na jina la flag
)
args = parser.parse_args()

# 2. Gevent Monkey Patching (Asynchronous execution)
# Lazima ifanyike kabla ya ku-import maktaba nyingine yoyote ya mtandao
if not args.disable_gevent:
    try:
        from gevent import monkey
        print(" * Importing gevent and monkey patching. Use --disable-gevent to disable.")
        monkey.patch_all()
    except ImportError:
        print(" * Gevent haijapatikana. Inaendelea bila monkey patching...")

# 3. Import CTFd App
# Import inafanyika hapa chini ili kuruhusu gevent kufanya kazi bila kuingiliwa
from CTFd import create_app

app = create_app()

# 4. Usanidi wa Profiling na Debugging (Kama umechagua --profile)
if args.profile:
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        import flask_profiler

        app.config["flask_profiler"] = {
            "enabled": True,
            "storage": {"engine": "sqlite"},
            "basicAuth": {"enabled": False},
            "ignore": ["^/themes/.*", "^/events"],
        }
        flask_profiler.init_app(app)
        app.config["DEBUG_TB_PROFILER_ENABLED"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        print(f" * Flask profiling running at http://0.0.0.0:{args.port}/flask-profiler/")
    except ImportError:
        print(" * Flask-Profiler au DebugToolbar hazijasakinishwa. Tumia 'pip install' kuzipata.")

# 5. Kuwasha Server
if __name__ == "__main__":
    print(f" * Establishing secure session on port {args.port}...")
    # host='0.0.0.0' ni MUHIMU kwa Codespaces na ufikiaji wa nje ya mashine yako
    app.run(debug=True, threaded=True, host="0.0.0.0", port=args.port)