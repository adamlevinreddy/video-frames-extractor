
from pathlib import Path
import fire
import frame_extractor_multithread as frame_extractor
import settings
from web_app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, threaded=True)
