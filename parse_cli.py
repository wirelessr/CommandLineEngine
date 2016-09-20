import sys
import re

from antlr4 import *
from antlr4.InputStream import InputStream

from ZyshLexer import ZyshLexer
from ZyshParser import ZyshParser
from ZyshVisitor import ZyshVisitor

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
	def __init__(self, isArg=False):
		self.sym_dict = {}
		self.isArg = isArg
		self.func = ""

global_entry = Entry()
func_list = []
sym_list = []

class DefPhase(ZyshVisitor):
	def __init__(self, global_entry, sym_list, func_list):
		self.tree_property = {}
		self.global_entry = global_entry
		self.sym_list = sym_list
		self.func_list = func_list
		self.func = ""
		self.memory = []
		self.hasArg2 = False

	def getValue(self, node):
		return self.tree_property[node]

	def setValue(self, node, value):
		self.tree_property[node] = value

	def visitVarDecl(self, ctx):
		name = ctx.meta().getText()
		self.setValue(ctx, name)
		item = self.visit(ctx.syntax())

		if item not in self.sym_list:
			self.sym_list.append(item)

	def visitRangeSyntax(self, ctx):
		ranges = ctx.RANGES().getText()
		min_num, max_num = ranges[2:-2].split("..") # trim the ("<) and (">)
		name = self.getValue(ctx.parentCtx)
		return Range(name, min_num, max_num)

	def visitMetaSyntax(self, ctx):
		syntax = ctx.getText()
		name = self.getValue(ctx.parentCtx)
		return Meta(name, syntax[1:-1]) # trim the double-quotes(")

	def visitBlock(self, ctx):
		return (ctx.privilege().INT().getText(), ctx.visibility().INT().getText(), ctx.function().SYMBOL().getText())

	def visitFunctionDecl(self, ctx):
		privilege, visibility, function = self.visit(ctx.block())

		if function not in self.func_list:
			self.func_list.append(function)
		self.func = function

		for symbols in ctx.symbols():
			
			current_entry = self.global_entry
			
			for sym in symbols.sym():
				sym_str = sym.getText()

				if sym_str not in self.sym_list:
					self.sym_list.append(Sym(sym_str))
				
				sym_id = self.sym_list.index(sym_str)

				if sym_id not in current_entry.sym_dict:
					entry = Entry()
					current_entry.sym_dict[sym_id] = entry
					current_entry = entry
				else:
					current_entry = current_entry.sym_dict[sym_id]
			
			self.setValue(symbols, current_entry)
			self.visit(symbols.arg())

	def goBackwardArg(self, ctx, sym_str):
		parent_entry = self.getValue(ctx.parentCtx)
		sym_id = self.sym_list.index(sym_str)

		if sym_id not in parent_entry.sym_dict:
			entry = Entry(True)
			parent_entry.sym_dict[sym_id] = entry
			current_entry = entry
		else:
			current_entry = parent_entry.sym_dict[sym_id]
		
		if len(ctx.arg()) == 0:
			if not self.hasArg2:
				current_entry.func = self.func
			self.memory.append(current_entry)
			return 

		self.setValue(ctx, current_entry)

		for arg in ctx.arg():
			self.visit(arg)

	def visitSymbolArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)

		sym_str = ctx.SYMBOL().getText()
		if sym_str not in self.sym_list:
			self.sym_list.append(Sym(sym_str))
		
		self.goBackwardArg(ctx, sym_str)

	def visitRangeArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)

		ranges = ctx.RANGE_SYMBOL().getText()
		min_num, max_num = ranges[1:-1].split("..") # trim the (<) and (>)

		new_item = Range(ranges, min_num, max_num)
		if new_item not in self.sym_list:
			self.sym_list.append(new_item)
		
		self.goBackwardArg(ctx, ranges)

	def visitOptionArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)
		
		self.memory.append(parent_entry)
		parent_entry.func = self.func

		self.setValue(ctx, parent_entry)
		self.visit(ctx.arg())

	def visitAlternArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)
	
		self.memory = []
		if ctx.arg2() is not None:
			self.hasArg2 = True

		self.setValue(ctx, parent_entry)
		for arg in ctx.arg():
			self.visit(arg)

		if ctx.arg2() is not None:
			cache_memory = self.memory[:]
			for entry in cache_memory:
				self.setValue(ctx, entry)
				self.hasArg2 = False
				self.visit(ctx.arg2())

	def visitArg2(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)

		self.setValue(ctx, parent_entry)
		self.visit(ctx.arg())
		

	def visitFinish(self):
		f = open('cmd_func.c', 'w')

		for func in self.func_list:
			f.write("extern int %s(int, char **);\n"%func) 
		f.write("typedef int (* cmd_func_t)(int, char **);\ncmd_func_t cmd_func[] = {\n")		
		for func in self.func_list:
			f.write("\t%s,\n"%func) 
		f.write("};")

		f = open('symbols.h', 'w')
		i = 0
		for sym in self.sym_list:
			f.write("#define %s %d\n"%(sym.define, i))
			i = i + 1


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

# definition phase, collect data
visitor = DefPhase(global_entry, sym_list, func_list)
result = visitor.visit(tree)

visitor.visitFinish()

