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
		self.g4 = "'%s'"%id
		self.type = "Sym"
	
	def __eq__(self, other):
		if type(other) is str:
			return self.name == other
		return self.name == other.name	
		
class Meta(Sym):
	def __init__(self, id, syntax):
		self.define = "META_%s"%id.upper()
		self.name = id
		self.meta = syntax
		self.g4 = self.define+"=meta_"
		self.type = "Meta"
	
	def rule(self):
		return self.meta

class Range(Sym):
	def __init__(self, id, min, max):
		self.define = "RANGE_%s_%s"%(min, max)
		self.name = id
		self.min = int(min)
		self.max = int(max)
		self.g4 = self.define+"=range_"
		self.type = "Range"
		
	def rule(self):
		return self.define
	
	def __eq__(self, other):
		if type(other) is str:
			return self.name == other
		return self.name == other.name	
				
func_list = []
sym_list = []
helper_dict = {}

class DefPhase(ZyshVisitor):
	def __init__(self, sym_list, func_list):
		self.sym_list = sym_list
		self.func_list = func_list
		self.temp = None
		self.rule_map = {}
		self.meta_map = {}
		self.arg_map = {}

	def visitHelper(self, ctx):
		helper = ctx.getText()
		return helper[1:-1] # trim the double-quotes(")

	def visitVarDecl(self, ctx):
		name = ctx.meta().getText()
		self.temp = name
		item = self.visit(ctx.syntax())
		item.helper = self.visit(ctx.helper())

		if item not in self.sym_list:
			self.sym_list.append(item)
		else:
			print("WARNING:", name, "is redefined")
			
		if item.define not in self.meta_map:
			self.meta_map[item.define] = item.rule()
	
	def visitHelpDecl(self, ctx):
		global helper_dict
		helper_dict[ctx.getText()] = self.visit(ctx.helper())

	def visitRangeSyntax(self, ctx):
		ranges = ctx.RANGES().getText()
		min_num, max_num = ranges[2:-2].split("..") # trim the ("<) and (">)
		name = self.temp
		return Range(name, min_num, max_num)

	def visitMetaSyntax(self, ctx):
		syntax = ctx.getText()
		name = self.temp
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

		func_rule = "func_" + function

		for symbols in ctx.symbols():
			rule_context = ""

			for sym in symbols.sym():
				sym_str = sym.getText()

				if sym_str not in self.sym_list:
					self.sym_list.append(Sym(sym_str))
				
				sym_id = self.sym_list.index(sym_str)

				rule_context += (" " + self.sym_list[sym_id].g4)
			
			if symbols.arg() is not None:
				index = self.rule_map.get(func_rule, "").count(func_rule + "_arg_")
				arg_rule = func_rule + "_arg_%d"%index

				self.temp = arg_rule
				self.arg_map[arg_rule] = []

				arg_context = self.visit(symbols.arg())

				self.rule_map[arg_rule] = arg_context
				rule_context += (" " + "ARG="+arg_rule + "\n")

			if func_rule not in self.rule_map:
				self.rule_map[func_rule] = rule_context
			else:
				self.rule_map[func_rule] += ("\t| " + rule_context)

	def visitSymbolArg(self, ctx):
		sym_str = ctx.SYMBOL().getText()
		if sym_str not in self.sym_list:
			self.sym_list.append(Sym(sym_str))
		
		sym_id = self.sym_list.index(sym_str)

		if not self.sym_list[sym_id].define.startswith("SYM_"):
			self.arg_map[self.temp].append(self.sym_list[sym_id])

		full_rule = self.sym_list[sym_id].g4 

		if ctx.arg() is not None:
			full_rule += (" " + self.visit(ctx.arg()))
		
		return full_rule

	def visitRangeArg(self, ctx):
		ranges = ctx.RANGE_SYMBOL().getText()
		min_num, max_num = ranges[1:-1].split("..") # trim the (<) and (>)

		new_item = Range(ranges, min_num, max_num)
		new_item.helper = ranges
		if new_item not in self.sym_list:
			self.sym_list.append(new_item)

		if new_item.define not in self.meta_map:
			self.meta_map[new_item.define] = new_item.rule()
		
		sym_id = self.sym_list.index(new_item)

		if self.sym_list[sym_id] not in self.arg_map[self.temp]:
			self.arg_map[self.temp].append(self.sym_list[sym_id])

		full_rule = self.sym_list[sym_id].g4

		if ctx.arg() is not None:
			full_rule += (" " + self.visit(ctx.arg()))

		return full_rule

	def visitOptionArg(self, ctx):
		arg_rule = []
		for arg in ctx.arg():
			arg_rule.append(self.visit(arg))
		arg_rule.sort()

		full_rule = "("
		full_rule += " | ".join(arg_rule)
		full_rule += ")?"

		if ctx.arg2() is not None:
			full_rule += (" " + self.visit(ctx.arg2()))

		return full_rule

	def visitAlternArg(self, ctx):
		arg_rule = []
		for arg in ctx.arg():
			arg_rule.append(self.visit(arg))
		arg_rule.sort()

		full_rule = "("
		full_rule += " | ".join(arg_rule)
		full_rule += ")"

		if ctx.arg2() is not None:
			full_rule += (" " + self.visit(ctx.arg2()))

		return full_rule


	def visitArg2(self, ctx):
		return self.visit(ctx.arg())

	def generate_g4(self):
		file_context = "grammar Cooked;\n\
@header {\n\
import re as regExp\n\
}\n\
top: ("
		for i in range(len(self.func_list)):
			if i != 0:
				file_context += " | "
			file_context += ("func_" + self.func_list[i])
		file_context += ")+ ;\n"
			
		for rule in self.rule_map:
			file_context += (rule + " : " + self.rule_map[rule] + ";\n")
		
		file_context += "\n\
range_ : INT ;\n\
meta_ : TEXT ;\n\
INT :   '0' | '1'..'9' '0'..'9'* ;\n\
TEXT : ~[ \\n\\r]+ ;\n\
WS  :   [ \\t\\n\\r]+ -> skip ;\n"

		#print(file_context)
		f = open('Cooked.g4', 'w')
		f.write(file_context)

	def generate_py(self):
		f = open('CookedHandler.template', 'r')
		file_template = f.read().split("[VisitFunctions]")

		file_context = file_template[0]

		file_context += "\n\
		self.func_list = [\"" + "\", \"".join(self.func_list) + "\"]\n\
		self.meta_map = {}\n"
		
		for meta in self.meta_map:
			file_context += "\n\
		self.meta_map[\"%s\"] = \"%s\"\n"%(meta, self.meta_map[meta])
			
		for func in self.func_list:
			file_context += "\n\
	def visit%s(self, ctx):\n\
		if not self.visit(ctx.ARG):\n\
			return [-1]\n\
		return self.visitTemplate(ctx, self.func_list)\n\
\n\
"%("Func_" + func)
		
		for arg in self.arg_map:
			file_context += "\n\
	def visit%s(self, ctx):\n\
"%(arg.capitalize())
			for meta in self.arg_map[arg]:
				file_context += "\n\
		if ctx.{0} is not None and not self.match_{1}(self.meta_map[\"{0}\"], ctx.{0}.getText()):\n\
			return False\n".format(meta.define, meta.type)
			file_context += "\n\
		return True\n"

		file_context += file_template[-1]
		
		
		# print(file_context)
		f = open('CookedHandler.py', 'w')
		f.write(file_context)

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
		
		self.generate_g4()
		self.generate_py()

input_stream = FileStream("test.cli")

lexer = ZyshLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = ZyshParser(token_stream)
tree = parser.top()

# lisp_tree_str = tree.toStringTree(recog=parser)
# print(lisp_tree_str)

# definition phase, collect data
visitor = DefPhase(sym_list, func_list)
result = visitor.visit(tree)

visitor.visitFinish()

# listEntryTree(global_entry)

