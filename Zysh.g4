grammar Zysh;

top:   (functionDecl | varDecl | helpDecl | filterDecl)+ ;

varDecl
    :   '%define' meta syntax helper ';'
    ;

helpDecl
	:	'%help' helpsym helper ';'
	;

functionDecl
    :   '%command' symbols (';' symbols)* '=' block
	|   '%reserved' symbols (';' symbols)* '=' block
    ;	
	
filterDecl
	:	'%filter' symbols '=' block
	;

symbols: sym+ ('%' arg)? ;
sym: SYMBOL ;
meta: SYMBOL ;
arg : SYMBOL arg?			# symbolArg
	| RANGE_SYMBOL arg?		# rangeArg
	| '[' arg ('|' arg)* ']' arg3?	# optionArg
	| '{' arg ('|' arg)* '}' arg2?	# alternArg
	;
arg2: arg ;
arg3: arg ;
block:  '{' block_attr+ '}' ;

block_attr 
	: privilege
	| visibility
	| function
	;

privilege: '%privilege' INT	';' ;
visibility: '%visibility' INT ';' ;
function: '%function' SYMBOL ';' ;

DIGIT: [0-9] ;
INT :   [0-9]+ ;
	
fragment
LETTER : [a-zA-Z] ;

syntax : RANGES # rangeSyntax
       | STRING	# metaSyntax
       ;

helper : RANGES
	| STRING 
	;
helpsym : SYMBOL
	| RANGE_SYMBOL
	;
RANGES : '"<' INT '..' INT '>"' ;
STRING :  '"' (ESC | ~'"')* '"' ;
SYMBOL : (LETTER | DIGIT | '_' | '-')+ ;
RANGE_SYMBOL : '<' INT ' '* '..' ' '* INT '>' ;

fragment ESC :   '\\' ["\\] ;

WS  :   [ \t\n\r]+ -> skip ;

SL_COMMENT
    :   '//' .*? '\n' -> skip
    ;
