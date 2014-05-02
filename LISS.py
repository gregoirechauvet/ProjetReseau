import sublime, sublime_plugin, socket, select

client = 0
views = []
cursors = []
old = []
data = 0
dataReceived = 0

HOST = 'localhost'
PORT = 5002
BUFFER = 4096

class ListenCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global client
		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client.connect((HOST, PORT))
		client.send("Socket initialized".encode())
		self.view.run_command('add_view')

class AddViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global client, views, cursors, data, dataReceived
		if client != 0:
			if self.view not in views:
				views.append(self.view)
				cursors.append([])
				old.append([])
				client.send("View added".encode())

		def Listen():
			global client, data, dataReceived
			while 1:
				read, write, errors = select.select([client], [], [])
				for sock in read:
					data = sock.recv(BUFFER)
					if data:
						data = data.decode()
						print('Data received')
						if data[0:1] == "i":
							self.view.run_command('insertion')
							dataReceived = 1
						elif data[0:1] == "d":
							self.view.run_command('deletion')
							dataReceived = 1

		sublime.set_timeout_async(Listen, 0)
		
class InsertionCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global data
		self.view.insert(edit, int(data[1:].split(",", 2)[0]), data[1:].split(",", 2)[1])
		# self.view.replace(edit, region, sublime.Region(begin_region_point, end_region_point))

class DeletionCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global data

class ListenerCommand(sublime_plugin.EventListener):
	def on_modified(self, view):
		global client, views, cursors, dataReceived
		if client != 0:
			if view in views:
				if dataReceived == 0:
					e = views.index(view)
					for i in range(len(view.sel())):
						if cursors[e][i].begin() < view.sel()[i].begin():
							client.send(("i" + str(cursors[e][i].begin()) + "," + view.substr(sublime.Region(cursors[e][i].begin() + i, view.sel()[i].begin()))).encode())
						else:
							client.send(("d" + str(view.sel()[i].begin()) + "," + str(cursors[e][i].begin())).encode())
				else:
					dataReceived = 0

	def on_selection_modified(self, view):
		global views, cursors, old
		if view in views:
			cursors[views.index(view)] = list(view.sel())