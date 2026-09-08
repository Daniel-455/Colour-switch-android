# Color Switch — Android project

This is the Android version of the existing Color Switch game. The original game logic was based on the user's Tkinter version; the UI was ported to Kivy because Tkinter is a desktop GUI toolkit and is not suitable for an Android APK.

## Build on GitHub

1. Create a GitHub repository.
2. Upload all files in this folder.
3. Open **Actions** in the repository.
4. Run the **Build Android APK** workflow.
5. Download the generated APK from the workflow run's **Artifacts** section.

## Files
- `main.py` — Android-compatible Kivy game.
- `buildozer.spec` — Android build configuration.
- `original_tkinter_version.py` — backup of the earlier game source.
