import re

class VisitTemplate:
	def __init__(self, meta_map):
		self.meta_map = meta_map
	
	def visitTemplate(self, ctx):
		args = []
		for child in ctx.getChild(ctx.getChildCount()-1).getChildren():
			args.append(child.getText().encode())
		print("visitTemplate with args", args)
		return args
	
	# meta_list : list(tuple(metaName:str, funcIdx:int))
	def match_metas(self, token, meta_list):
		ret_set = set()

		for metaName, funcIdx in meta_list:
			if self.match_meta(token, metaName):
				ret_set.add(funcIdx)

		return ret_set
			
	def match_meta(self, token, meta):
		if meta.startswith("RANGE_"):
			min_, max_ = meta[6:].split("_")
			if int(min_) <= int(token) <= int(max_):
				return True
			return False
		elif meta.startswith("META_"):
			if re.match(self.meta_map[meta], token) is None:
				print("match_Meta fail: %s %s"%(self.meta_map[meta], token))
				return False
			return True
		return False

