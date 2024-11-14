import customtkinter as ctk
from controller.Controller import Controller

def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Analísis de Precipitación")

    root.geometry("1280x720")

    root.columnconfigure(2, weight=1)
    root.rowconfigure(2, weight=1)
    
    app = Controller(root)
    
    w = 1280 
    h = 720
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight() 
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.resizable(False, False)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.mainloop()

if __name__ == "__main__":
    main()
