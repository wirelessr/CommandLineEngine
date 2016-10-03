class VisitTemplate:
	def __init__(self, ruleNames):
		self.ruleNames = ruleNames
	
	def visitTemplate(self, ctx):
		print("visitTemplate")
		ruleName = self.ruleNames[ctx.getRuleIndex()]

		args = []
		for child in ctx.getChild(ctx.getChildCount()-1).getChildren():
			args.append(child.getText())
		print("function :", ruleName+"()", "with arg :", args)
		
