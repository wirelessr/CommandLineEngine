import sys

from antlr4 import *
from antlr4.InputStream import InputStream

from ZyshLexer import ZyshLexer
from ZyshParser import ZyshParser
from ZyshListener import ZyshListener

class Entry:
	def __init__(self):
		self.sym_dict = {}
		self.isArg = False
		self.func = ""

global_entry = Entry()
func_list = []
sym_list = []
meta_list = []

def inMetaList(metasym, mlist):
	for (x, y) in mlist:
		if x == metasym:
			return mlist.index((x, y))
	return None

class DefPhase(ZyshListener):
	def __init__(self):
		self.entry = Entry()
		self.stack = []

		f = open('cmd_func.c', 'w')
		f.write("typedef int (* cmd_func_t)(int, char **);\ncmd_func_t cmd_func[] = {\n")		
		f.close()
	
	def exitMeta(self, ctx):
		self.stack.append(ctx.SYMBOL().getText())

	def exitVarDecl(self, ctx):
		global meta_list
		meta = self.stack.pop()

		if inMetaList(meta, meta_list) is None:
			meta_list.append((meta, ctx.SYNTAX().getText()))

	def enterFunctionDecl(self, ctx):
		global global_entry
		self.entry = global_entry

	def exitFunction(self, ctx):
		global func_list
		self.entry.func = ctx.SYMBOL().getText()

		if self.entry.func not in func_list:
			with open('cmd_func.c', 'r') as original: data = original.read()
			with open('cmd_func.c', 'w') as modified: modified.write("extern int %s(int, char **);\n"%(self.entry.func) + data + '\t' + self.entry.func + ',\n')
			func_list.append(self.entry.func)
	
	def exitArg(self, ctx):
		self.exitSym(ctx)
		self.entry.isArg = True

	def exitSym(self, ctx):
		global meta_list
		global sym_list
		current_sym = ctx.SYMBOL().getText()
		
		meta_id = inMetaList(current_sym, meta_list)
		if meta_id is None:
			if current_sym not in sym_list:
				sym_list.append(current_sym)
			current_id = sym_list.index(current_sym)
		else:
			current_id = meta_id

		if current_id not in self.entry.sym_dict:
			new_entry = Entry()
			self.entry.sym_dict[current_id] = new_entry
			self.entry = new_entry
		else:
			self.entry = self.entry.sym_dict.get(current_id)
	
	def finish(self):
		global sym_list
		global meta_list
		i = 0
		f = open('cmd_func.c', 'a')
		f.write("};\n")		
		f.close()

		f = open('symbols.h', 'w')
		for sym in sym_list:
			f.write("#define SYM_%s %d\n"%(sym.upper(), i))
			i = i + 1
		for meta, syntax in meta_list:
			f.write("#define META_%s %d\n"%(meta.upper(), i))
			i = i + 1
		f.close()

def match_meta(s):
	global meta_list

	for (x, y) in meta_list:
		if s in y:
			return meta_list.index((x, y))
	return None

def cli_exec(zysh_cli):
	global global_entry
	global func_list
	global sym_list
	arg_list = []

	print('*** CLI ***')
	zysh_cli = zysh_cli.decode("utf8")
	print(zysh_cli)
	
	current_entry = global_entry
	for s in zysh_cli.split():
		if s in sym_list:
			idx = sym_list.index(s)
		else:
			idx = match_meta(s)

		current_entry = current_entry.sym_dict[idx]
		if current_entry.isArg:
			arg_list.append(s.encode())
			
	
	arg_list.insert(0, func_list.index(current_entry.func))
	print("uses ", current_entry.func, "(", arg_list, ")")
	return arg_list



input_stream = FileStream("test.cli")

lexer = ZyshLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = ZyshParser(token_stream)
tree = parser.top()

# lisp_tree_str = tree.toStringTree(recog=parser)
# print(lisp_tree_str)

walker = ParseTreeWalker()

# definition phase, collect data
def_phase = DefPhase()
walker.walk(def_phase, tree)
def_phase.finish()
	

