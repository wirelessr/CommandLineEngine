import re

class VisitTemplate:
	def __init__(self, ruleNames):
		self.ruleNames = ruleNames
	
	def visitTemplate(self, ctx, func_list):
		print("visitTemplate")
		ruleName = self.ruleNames[ctx.getRuleIndex()]
		funcName = ruleName[5:]
		
		args = [func_list.index(funcName)]
		for child in ctx.getChild(ctx.getChildCount()-1).getChildren():
			args.append(child.getText().encode())
		print("function :", funcName+"()", "with arg :", args)
		return args
		
	def match_Meta(self, meta, token):
		if re.match(meta, token) is None:
			print("match_Meta fail: %s %s"%(meta, token))
			return False
		return True
	
	def match_Range(self, range_, token):
		# range_ = "RANGE_X_Y"
		min_, max_ = range_[6:].split("_")
		if int(min_) <= int(token) <= int(max_):
			return True
		return False
