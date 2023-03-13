from tkinter import *
import webbrowser
from model import route

root = Tk()
frame = Frame(root)
frame.pack()


def Open():
    webbrowser.open_new('http://127.0.0.1:8080')
    route.start()


button = Button(frame, text="CLICK", command=Open())

button.pack()
root.mainloop()
