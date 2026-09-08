"""Modal dialog utilities for centering, input grabbing, and flash alert notifications."""

import ctypes
import tkinter as tk
import customtkinter as ctk

def flash_window(toplevel: ctk.CTkToplevel):
    """Flashes the window caption/taskbar in Windows and sounds the system bell."""
    try:
        toplevel.bell()
    except Exception:
        pass
        
    try:
        toplevel.lift()
    except Exception:
        pass

    try:
        hwnd = toplevel.winfo_id()
        parent_hwnd = ctypes.windll.user32.GetParent(hwnd)
        target_hwnd = parent_hwnd if parent_hwnd else hwnd
        ctypes.windll.user32.FlashWindow(target_hwnd, True)
    except Exception:
        pass


def setup_modal_dialog(
    dialog: ctk.CTkToplevel,
    parent,
    target_width: int,
    target_height: int,
    resizable: bool = False,
    min_width: int = None,
    min_height: int = None,
):
    """
    Centers the dialog on screen, locks parent input (modal grab),
    keeps it on top, and flashes/alerts whenever the user attempts to click the parent.
    """
    root = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
    
    # 1. Transient to top-level root window
    dialog.transient(root)
    dialog.attributes("-topmost", True)
    
    # Use super().resizable to prevent CustomTkinter from triggering duplicate withdraw/color calls
    if not resizable:
        super(ctk.CTkToplevel, dialog).resizable(False, False)
    else:
        super(ctk.CTkToplevel, dialog).resizable(True, True)

    # 2. Responsive Screen Centering
    dialog.update_idletasks()
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()

    w = min(target_width, int(sw * 0.92))
    h = min(target_height, int(sh * 0.88))
    
    mw = min(min_width or w, w)
    mh = min(min_height or h, h)
    dialog.minsize(mw, mh)

    x = max(10, (sw - w) // 2)
    y = max(20, (sh - h) // 2 - 15)
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    # 3. Explicitly deiconify, lift and set focus
    dialog.deiconify()
    dialog.lift()
    dialog.focus_force()
    
    def ensure_grab():
        try:
            if dialog.winfo_exists():
                dialog.deiconify()
                dialog.attributes("-topmost", True)
                dialog.lift()
                dialog.focus_force()
                dialog.grab_set()
        except Exception:
            pass
            
    dialog.after(60, ensure_grab)

    # 4. Intercept clicks and focus on root window while modal is open
    def on_parent_click(event=None):
        if dialog.winfo_exists() and dialog.winfo_ismapped():
            flash_window(dialog)
            dialog.lift()
            return "break"

    def on_root_focus(event):
        if event.widget == root and dialog.winfo_exists() and dialog.winfo_ismapped():
            flash_window(dialog)

    bind_btn = root.bind("<Button-1>", on_parent_click, add="+")
    bind_focus = root.bind("<FocusIn>", on_root_focus, add="+")

    def on_destroy(event):
        if event.widget == dialog:
            try:
                root.unbind("<Button-1>", bind_btn)
            except Exception:
                pass
            try:
                root.unbind("<FocusIn>", bind_focus)
            except Exception:
                pass
            try:
                root.focus_force()
            except Exception:
                pass

    dialog.bind("<Destroy>", on_destroy, add="+")
