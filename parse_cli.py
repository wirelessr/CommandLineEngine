import sys
import re

from antlr4 import *
from antlr4.InputStream import InputStream

from ZyshLexer import ZyshLexer
from ZyshParser import ZyshParser
from ZyshListener import ZyshListener

class Sym:
	def __init__(self, id):
		self.name = id
		self.define = "SYM_%s"%id.upper()
	
	def match(self, token):
		return token == self.name
	
	def __eq__(self, other):
		if type(other) is str:
			return self.name == other
		return self.name == other.name	
		
class Meta(Sym):
	def __init__(self, id, syntax):
		self.define = "META_%s"%id.upper()
		self.name = id
		self.meta = syntax
	
	def match(self, token):
		if re.match(self.meta, token) is None:
			return False
		return True

class Range(Sym):
	def __init__(self, id, min, max):
		self.define = "RANGE_%s_%s"%(min, max)
		self.name = id
		self.min = int(min)
		self.max = int(max)
	
	def match(self, token):
		try:
			num = int(token)
		except ValueError:
			return False
			
		if self.min <= num <= self.max:
			return True
		return False
	
class Entry:
	def __init__(self):
		self.sym_dict = {}
		self.isArg = False
		self.func = ""

global_entry = Entry()
func_list = []
sym_list = []

class DefPhase(ZyshListener):
	def __init__(self):
		self.entry = Entry()
		self.item = None
		self.name = ""

		f = open('cmd_func.c', 'w')
		f.write("typedef int (* cmd_func_t)(int, char **);\ncmd_func_t cmd_func[] = {\n")		
		f.close()
	
	def enterVarDecl(self, ctx):
		self.name = ctx.meta().getText()

	def exitRangeSyntax(self, ctx):
		ranges = ctx.RANGES().getText()
		min_num, max_num = ranges[2:-2].split("..") # trim the ("<) and (">)
		self.item = Range(self.name, min_num, max_num)

	def exitMetaSyntax(self, ctx):
		syntax = ctx.getText()
		self.item = Meta(self.name, syntax[1:-1]) # trim the double-quotes(")
		
	def exitVarDecl(self, ctx):
		global sym_list

		if self.item not in sym_list:
			sym_list.append(self.item)

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
	
	def exitSymbolArg(self, ctx):
		self.exitSymStr(ctx.SYMBOL().getText())
		self.entry.isArg = True

	def exitRangeArg(self, ctx):
		global sym_list

		ranges = ctx.RANGE_SYMBOL().getText()
		min_num, max_num = ranges[1:-1].split("..") # trim the (<) and (>)

		new_item = Range(ranges, min_num, max_num)
		if new_item not in sym_list:
			sym_list.append(new_item)

		self.exitSymStr(ranges)
		self.entry.isArg = True

	def exitSym(self, ctx):
		self.exitSymStr(ctx.SYMBOL().getText())

	def exitSymStr(self, current_sym):
		global sym_list
		
		if current_sym not in sym_list:
			sym_list.append(Sym(current_sym))
		current_id = sym_list.index(current_sym)
		
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
			f.write("#define %s %d\n"%(sym.define, i)) # FIXME : when different symbols(RANGE) are the same range, it must cause re-define
			i = i + 1
		f.close()

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
		for sym_id in current_entry.sym_dict:
			if sym_list[sym_id].match(s):
				current_entry = current_entry.sym_dict[sym_id]
				break
		else:
			current_entry = None

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
	

