# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import sys

version = sys.hexversion
if version >= 0x020600F0 and version < 0x03000000 :
	py2 = True	# Python 2.6 or 2.7
	from Tkinter import *
	import ttk
else:
	print ("""
	You do not have a version of python supporting ttk widgets..
	You need a version >= 2.6 to execute blockBox GUI.
	""")
	sys.exit()

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