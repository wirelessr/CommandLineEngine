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
		
