import re

from antlr4 import *
from antlr4.InputStream import InputStream

from ZyshLexer import ZyshLexer
from ZyshParser import ZyshParser
from ZyshVisitor import ZyshVisitor

"""
terminated_map
	key : tuple(TagStr, idx:int)
	val : list(tag_idx:str)

tag_map
	key : tag_idx:str
	val : list(TagStr.meta)

TagStr.meta
	list(tuple(MetaName:str, FuncIdx:int))

"""
class TagStr(str):
	def __new__(cls, value, meta):
		obj = str.__new__(cls, value)
		obj.meta = meta
		return obj

class Sym:
	def __init__(self, id):
		self.name = id
		self.define = "SYM_%s"%id.upper()
		self.helper = id
		self.g4 = "'%s'"%id
		self.type = "Sym"
	
	def tag(self, func):
		return []

	def __eq__(self, other):
		if type(other) is str:
			return self.name == other
		return self.name == other.name	
		
class Meta(Sym):
	def __init__(self, id, syntax):
		self.define = "META_%s"%id.upper()
		self.name = id
		self.meta = syntax
		self.g4 = "meta_"
		self.type = "Meta"
	
	def tag(self, func):
		return [(self.define, func)]

	def rule(self):
		return self.meta

class Range(Sym):
	def __init__(self, id, min, max):
		self.define = "RANGE_%s_%s"%(min, max)
		self.name = id
		self.min = int(min)
		self.max = int(max)
		self.g4 = "range_"
		self.type = "Range"
		
	def tag(self, func):
		return [(self.define, func)]

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
		self.cmd_map = {}
		self.meta_map = {}
		self.tag_map = {}
		self.terminated_map = {}
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
		self.temp = self.func_list.index(function)

		for symbols in ctx.symbols():
			prefix = ""

			for sym in symbols.sym():
				sym_str = sym.getText()

				if sym_str not in self.sym_list:
					self.sym_list.append(Sym(sym_str))
				
				sym_id = self.sym_list.index(sym_str)

				prefix += (" " + self.sym_list[sym_id].g4)
			
			if self.cmd_map.get(prefix) is None:
				self.cmd_map[prefix] = []

			teminated = TagStr("TERMINATED", [function])
			if symbols.arg() is not None:
				arg_context = self.visit(symbols.arg())
				arg_context.append(teminated)
			else:
				arg_context = [teminated]


			if arg_context in self.cmd_map[prefix]:
				exist_idx = self.cmd_map[prefix].index(arg_context)
				self.mergeMetaList(self.cmd_map[prefix][exist_idx], arg_context)
			else:
				self.cmd_map[prefix].append(arg_context)



	def visitSymbolArg(self, ctx):
		sym_str = ctx.SYMBOL().getText()
		if sym_str not in self.sym_list:
			self.sym_list.append(Sym(sym_str))
		
		sym_id = self.sym_list.index(sym_str)

		full_rule = [TagStr(self.sym_list[sym_id].g4, self.sym_list[sym_id].tag(self.temp))]

		if ctx.arg() is not None:
			full_rule += self.visit(ctx.arg())
		
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

		full_rule = [TagStr(self.sym_list[sym_id].g4, self.sym_list[sym_id].tag(self.temp))]

		if ctx.arg() is not None:
			full_rule += self.visit(ctx.arg())

		return full_rule


	def mergeMetaList(self, orig, other):
		for i in range(len(orig)):
			orig[i].meta += other[i].meta

	def visitMultiArg(self, ctx, option=""):
		arg_rules = []
		for arg in ctx.arg():
			arg_rule = self.visit(arg)
			
			if arg_rule in arg_rules:
				exist_idx = arg_rules.index(arg_rule)

				self.mergeMetaList(arg_rules[exist_idx], arg_rule)
			else:
				arg_rules.append(arg_rule)

		if len(arg_rules) > 1 or option != "":
			full_rule = ["("]
		else:
			full_rule = []

		for arg_rule in arg_rules:
			if len(full_rule) > 1:
				full_rule += ["|"]
			full_rule += arg_rule

		if len(arg_rules) > 1 or option != "":
			full_rule += [")"+option]

		if ctx.arg2() is not None:
			full_rule += self.visit(ctx.arg2())

		return full_rule
		

	def visitOptionArg(self, ctx):
		return self.visitMultiArg(ctx, "?")

	def visitAlternArg(self, ctx):
		return self.visitMultiArg(ctx)


	def visitArg2(self, ctx):
		return self.visit(ctx.arg())


	def createRule(self):
		rule_idx = 0
		terminated_idx = 0
		tag_idx = 0

		for prefix in self.cmd_map:
			rule_key = "rule%d"%rule_idx
			rule_idx += 1

			arg_key = "%s_arg"%rule_key
			
			self.rule_map[rule_key] = ["%s ARG=%s"%(prefix, arg_key)]
			self.rule_map[arg_key] = []

			for rule in self.cmd_map[prefix]:
				rule_context = ""
				tag_list = []

				for token in rule:
					if token == "meta_" or token == "range_":
						tag_name = "TAG%d"%tag_idx
						tag_idx += 1

						rule_context += ("%s=%s "%(tag_name, token))
						self.tag_map[tag_name] = token.meta

						tag_list.append(tag_name)

					elif token == "TERMINATED":
						terminated_name = "TERMINATED%d"%terminated_idx

						rule_context += (token + " # " + terminated_name)
						self.terminated_map[(token, terminated_idx)] = tag_list

						terminated_idx += 1

					else:
						rule_context += (token + " ")
				
				self.rule_map[arg_key].append(rule_context)

	def generate_g4(self):
		rules = []
		for rule in self.rule_map:
			if not rule.endswith("_arg"):
				rules.append(rule)
		file_context = "grammar Cooked;\n\
top: (%s)+ ;\n"%" | ".join(rules)
			
		for rule in self.rule_map:
			file_context += (rule + " :\n")

			for i in range(len(self.rule_map[rule])):
				if i == 0:
					file_context += "    "
				else:
					file_context += "  | "

				file_context += (self.rule_map[rule][i] + "\n")

			file_context += "  ;\n"
		
		file_context += "\n\
range_ : INT ;\n\
meta_ : TEXT ;\n\
TERMINATED : '\\r'? '\\n' ;\n\
INT :   '0' | '1'..'9' '0'..'9'* ;\n\
TEXT : ~[ \\n\\r]+ ;\n\
WS  :   [ \\t\\r]+ -> skip ;\n"

		# print(file_context)
		f = open('Cooked.g4', 'w')
		f.write(file_context)

	def generate_py(self):
		f = open('CookedHandler.template', 'r')
		file_template = f.read()

		initVariables = ""
		visitFunctions = ""
		
		for meta in self.meta_map:
			initVariables += "\n\
		self.meta_map[\"%s\"] = \"%s\"\n"%(meta, self.meta_map[meta])


		for rule in self.rule_map:
			if not rule.endswith("_arg"):
				visitFunctions += "\n\
	def visit%s(self, ctx):\n\
		l = self.visit(ctx.ARG)\n\
		l += self.visitTemplate(ctx)\n\
		return l\n"%rule.capitalize()

		
		for terminated, idx in self.terminated_map:
			visitFunctions += "\n\
	def visit%s%d(self, ctx):\n"%(terminated, idx)
		
			if len(self.terminated_map[(terminated, idx)]) == 0:
				visitFunctions += "\
		return [%d]\n"%self.func_list.index(terminated.meta[0])
		
			else:
				visitFunctions += "\
		func_set = None\n"
				for tag in self.terminated_map[(terminated, idx)]:
					visitFunctions += "\
		if ctx.{0} is not None:\n\
			ret_set = self.match_metas(ctx.{0}, {1})\n\
			func_set = ret_set if func_set is None else func_set & ret_set\n".format(tag, str(self.tag_map[tag]))

				visitFunctions += "\
		if len(func_set) == 0:\n\
			return [-1]\n\
		return [func_set.pop()]\n"


		
		file_template = file_template.replace("[InitVariables]", initVariables)
		file_template = file_template.replace("[VisitFunctions]", visitFunctions)
		
		# print(file_template)
		f = open('CookedHandler.py', 'w')
		f.write(file_template)

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

visitor.createRule()
visitor.visitFinish()
# visitor.listRule()

# listEntryTree(global_entry)

