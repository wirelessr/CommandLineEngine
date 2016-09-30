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
	
	def __eq__(self, other):
		if type(other) is str:
			return self.name == other
		return self.name == other.name	
		
class Meta(Sym):
	def __init__(self, id, syntax):
		self.define = "META_%s"%id.upper()
		self.name = id
		self.meta = syntax
		self.g4 = "meta_%s"%id
	
	def rule(self):
		context = ("TEXT {\n\
meta_syntax = \"" + self.meta + "\"\n\
if regExp.match(meta_syntax, $TEXT.text) is None:\n\
	raise RecognitionException($TEXT.text + \" does not match \" + meta_syntax)\n\
}" )
		return context

class Range(Sym):
	def __init__(self, id, min, max):
		self.define = "RANGE_%s_%s"%(min, max)
		self.name = id
		self.min = int(min)
		self.max = int(max)
		self.g4 = self.define.lower()
		
	def rule(self):
		context = ("INT {\n\
if not %d <= $INT.int <= %d:\n\
	raise RecognitionException($INT.text + \" is not between %d and %d\")\n\
}"%(self.min, self.max, self.min, self.max) )
		return context

func_list = []
sym_list = []
helper_dict = {}

class DefPhase(ZyshVisitor):
	def __init__(self, sym_list, func_list):
		self.sym_list = sym_list
		self.func_list = func_list
		self.temp = None
		self.rule_map = {}

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
			self.rule_map[item.g4] = item.rule()
		else:
			print("WARNING:", name, "is redefined")
	
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

		rule_context = ""

		for i in range(len(ctx.symbols())):
			if i != 0:
				rule_context += "\t|"
			symbols = ctx.symbols()[i]
			for sym in symbols.sym():
				sym_str = sym.getText()

				if sym_str not in self.sym_list:
					self.sym_list.append(Sym(sym_str))
				
				sym_id = self.sym_list.index(sym_str)

				rule_context += (" " + self.sym_list[sym_id].g4)
			
			if symbols.arg() is not None:
				rule_context += (" " + self.visit(symbols.arg()) + "\n")

		func_rule = "func_" + function
		if func_rule not in self.rule_map:
			self.rule_map[func_rule] = rule_context
		else:
			self.rule_map[func_rule] += ("\t| " + rule_context)

	def visitSymbolArg(self, ctx):
		sym_str = ctx.SYMBOL().getText()
		if sym_str not in self.sym_list:
			self.sym_list.append(Sym(sym_str))
		
		sym_id = self.sym_list.index(sym_str)

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
		
		sym_id = self.sym_list.index(new_item)

		full_rule = self.sym_list[sym_id].g4

		if ctx.arg() is not None:
			full_rule += (" " + self.visit(ctx.arg()))

		return full_rule

	def visitOptionArg(self, ctx):
		arg_rule = []
		for arg in ctx.arg():
			arg_rule.append(self.visit(arg))

		full_rule = "("
		for i in range(len(arg_rule)):
			if i != 0:
				full_rule += " | "
			full_rule += (arg_rule[i])
		full_rule += ")?"

		if ctx.arg2() is not None:
			full_rule += (" " + self.visit(ctx.arg2()))

		return full_rule

	def visitAlternArg(self, ctx):
		arg_rule = []
		for arg in ctx.arg():
			arg_rule.append(self.visit(arg))

		full_rule = "("
		for i in range(len(arg_rule)):
			if i != 0:
				full_rule += " | "
			full_rule += (arg_rule[i])
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
		
		print(file_context)
		f = open('Cooked.g4', 'w')
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

