import sys
from ui.app import App

if __name__ == "__main__":
    app = None
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] Application closed by user (Ctrl+C). Cleaning up PLC connections...")
        if app:
            try:
                app.on_closing()
            except Exception:
                pass
        try:
            sys.exit(0)
        except SystemExit:
            pass