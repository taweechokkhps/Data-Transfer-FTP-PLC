import sys
from ui.app import App

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] Application closed cleanly by user (Ctrl+C).")
        try:
            sys.exit(0)
        except SystemExit:
            pass