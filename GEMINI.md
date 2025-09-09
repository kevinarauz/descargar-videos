## Project Overview

This project is a Python-based web application for downloading M3U8 videos. It features a Flask web interface for users to paste M3U8 URLs, play the videos, and download them as MP4 files.

The application is designed for high-speed downloading, utilizing up to 1000 concurrent workers. It provides real-time feedback on download progress, including speed, ETA, and segment-level progress.

A key feature of this project is its DRM (Digital Rights Management) research and decryption capabilities. The `drm_decryption_module.py` and `drm_research_module.py` files suggest that the application can be used for academic research into DRM protection. The `README_DRM_MODULE.md` likely contains more information on this.

The application also includes features like download queueing, history, and automatic cleanup of temporary files.

## Building and Running

### Dependencies

The Python dependencies for this project are listed in `requirements.txt`. However, this file appears to be corrupted or in an unreadable format. Based on the source code, the key dependencies are:

*   flask
*   requests
*   tqdm
*   cryptography

You can likely install them using pip:

```bash
pip install flask requests tqdm cryptography
```

### Running the Application

To start the web application, run the following command:

```bash
python app.py
```

The application will be available at `http://localhost:5000`.

### FFmpeg

The project requires FFmpeg for merging the downloaded video segments. You need to install FFmpeg and ensure it's available in your system's PATH.

## Development Conventions

*   **Code Style:** The Python code follows the PEP 8 style guide.
*   **Modularity:** The application is well-structured, with different functionalities separated into different modules (e.g., `m3u8_downloader.py`, `drm_decryption_module.py`, `app.py`).
*   **Configuration:** The application's configuration, such as the number of workers and logging settings, is managed in the `app.py` file.
*   **Logging:** The application uses the `logging` module for logging, with the ability to log to both the console and files.
*   **DRM Research:** The DRM-related modules are intended for academic research and should be used responsibly. The `README_DRM_MODULE.md` file should be consulted for more information on the DRM capabilities.
