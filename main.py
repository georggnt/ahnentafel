import tkinter as tk

from portrait_app import PortraitProApp

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except Exception:
    TkinterDnD = None
    DND_AVAILABLE = False


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    PortraitProApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
