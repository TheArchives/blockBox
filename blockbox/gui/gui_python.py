# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import sys

py2 = py30 = py31 = False
version = sys.hexversion
if version >= 0x020600F0 and version < 0x03000000 :
    py2 = True    # Python 2.6 or 2.7
    from Tkinter import *
    import ttk
elif version >= 0x03000000 and version < 0x03010000 :
    py30 = True
    from tkinter import *
    import ttk
elif version >= 0x03010000:
    py31 = True
    from tkinter import *
    import tkinter.ttk as ttk
else:
    print ("""
    You do not have a version of python supporting ttk widgets..
    You need a version >= 2.6 to execute blockBox GUI.
    """)
    sys.exit()



'''

    If you use the following functions, change the names 'w' and
    'w_win'.  Use as a template for creating a new Top-level window.

w = None
def create_New_Toplevel_1 ()
    global w
    global w_win
    if w: # So we have only one instance of window.
        return
    w = Toplevel (root)
    w.title('New Toplevel 1')
    w.geometry('849x540+69+55')
    w_win = New_Toplevel_1 (w)

   Template for routine to destroy a top level window.

def destroy():
    global w
    w.destroy()
    w = None
'''

def vp_start_gui():
    global val, w, root
    root = Tk()
    root.title('New_Toplevel_1')
    root.geometry('849x540+69+55')
    w = New_Toplevel_1 (root)
    init()
    root.mainloop()



def init():
    pass



def TODO():
    pass

class New_Toplevel_1:
    def __init__(self, master=None):
        # Set background of toplevel window to match
        # current style
        style = ttk.Style()
        theme = style.theme_use()
        default = style.lookup(theme, 'background')
        master.configure(background=default)

        self.m33 = Menu(master,font=())
        master.configure(menu = self.m33)
        self.m33.add_command(label="New command",command=TODO)


        self.can34 = Canvas (master)
        self.can34.place(relx=-0.01,rely=-0.02,relheight=1.04,relwidth=1.02)
        self.can34.configure(borderwidth="2")
        self.can34.configure(height="563")
        self.can34.configure(relief="ridge")
        self.can34.configure(width="866")