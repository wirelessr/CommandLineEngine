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
		self.helper = id
	
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
helper_dict = {}

def listEntryTree(entry, prefix=""):
	global sym_list
	for sym_id in entry.sym_dict:
		print(prefix, sym_list[sym_id].name)
		listEntryTree(entry.sym_dict[sym_id], prefix+"  ")

class DefPhase(ZyshVisitor):
	def __init__(self, global_entry, sym_list, func_list):
		self.tree_property = {}
		self.global_entry = global_entry
		self.sym_list = sym_list
		self.func_list = func_list
		self.func = ""
		self.memory2 = []
		self.memory3 = []
		self.hasArg2 = False
		self.hasArg3 = False

	def getValue(self, node):
		return self.tree_property[node]

	def setValue(self, node, value):
		self.tree_property[node] = value

	def visitHelper(self, ctx):
		helper = ctx.getText()
		return helper[1:-1] # trim the double-quotes(")

	def visitVarDecl(self, ctx):
		name = ctx.meta().getText()
		self.setValue(ctx, name)
		item = self.visit(ctx.syntax())
		item.helper = self.visit(ctx.helper())

		if item not in self.sym_list:
			self.sym_list.append(item)
		else:
			raise
	
	def visitHelpDecl(self, ctx):
		global helper_dict
		helper_dict[ctx.meta().getText()] = self.visit(ctx.helper())

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
		privilege = "100"
		visibility = "100"

		for block_attr in ctx.block_attr():
			ruleIdx = block_attr.getChild(0).getRuleIndex()
			
			if ruleIdx == ZyshParser.RULE_privilege:
				privilege = block_attr.privilege().INT().getText()
			elif ruleIdx == ZyshParser.RULE_visibility:
				visibility = block_attr.visibility().INT().getText()
			elif ruleIdx == ZyshParser.RULE_function:
				function = block_attr.function().SYMBOL().getText()

		return (privilege, visibility, function)

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
			
			if symbols.arg() is not None:
				self.setValue(symbols, current_entry)
				self.visit(symbols.arg())
			else:
				current_entry.func = function

	def goBackwardArg(self, ctx, sym_str):
		parent_entry = self.getValue(ctx.parentCtx)
		sym_id = self.sym_list.index(sym_str)

		if sym_id not in parent_entry.sym_dict:
			entry = Entry(True)
			parent_entry.sym_dict[sym_id] = entry
			current_entry = entry
		else:
			current_entry = parent_entry.sym_dict[sym_id]
		
		if ctx.arg() is None:
			if not self.hasArg2:
				current_entry.func = self.func
			self.memory2.append(current_entry)
			self.memory3.append(current_entry)
			return 

		self.setValue(ctx, current_entry)

		self.visit(ctx.arg())

	def visitSymbolArg(self, ctx):
		sym_str = ctx.SYMBOL().getText()
		if sym_str not in self.sym_list:
			self.sym_list.append(Sym(sym_str))
		
		self.goBackwardArg(ctx, sym_str)

	def visitRangeArg(self, ctx):
		ranges = ctx.RANGE_SYMBOL().getText()
		min_num, max_num = ranges[1:-1].split("..") # trim the (<) and (>)

		new_item = Range(ranges, min_num, max_num)
		new_item.helper = ranges
		if new_item not in self.sym_list:
			self.sym_list.append(new_item)
		
		self.goBackwardArg(ctx, ranges)

	def visitOptionArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)
		
		self.memory2.append(parent_entry)
		self.memory3.append(parent_entry)

		if ctx.arg3() is None:
			parent_entry.func = self.func
		else:
			self.hasArg3 = True
			self.memory3 = [parent_entry]

		self.setValue(ctx, parent_entry)
		for arg in ctx.arg():
			self.visit(arg)

		if ctx.arg3() is not None:
			cache_memory = self.memory3[:]
			for entry in cache_memory:
				self.setValue(ctx, entry)
				self.hasArg3 = False
				self.visit(ctx.arg3())

	def visitAlternArg(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)
	
		self.memory2 = []
		if ctx.arg2() is not None:
			self.hasArg2 = True

		self.setValue(ctx, parent_entry)
		for arg in ctx.arg():
			self.visit(arg)

		if ctx.arg2() is not None:
			cache_memory = self.memory2[:]
			for entry in cache_memory:
				self.setValue(ctx, entry)
				self.hasArg2 = False
				self.visit(ctx.arg2())

	def visitArg2(self, ctx):
		parent_entry = self.getValue(ctx.parentCtx)

		self.setValue(ctx, parent_entry)
		self.visit(ctx.arg())
		
	def visitArg3(self, ctx):
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
		if s == '?':
			arg_list = [-1]
			for sym_id in current_entry.sym_dict:
				arg_list.append(sym_list[sym_id].helper.encode())
			listEntryTree(global_entry)
			return arg_list

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

# listEntryTree(global_entry)

