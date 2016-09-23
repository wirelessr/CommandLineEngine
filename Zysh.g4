grammar Zysh;

top:   (functionDecl | varDecl | helpDecl | reserved)+ ;

varDecl
    :   '%define' meta syntax helper ';'
    ;

helpDecl
	:	'%help' meta helper ';'
	;

functionDecl
    :   '%command' symbols (';' symbols)* '=' block
    ;	
	
reserved
    :   '%reserved' symbols (';' symbols)* '=' block
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
block:  '{' privilege? visibility? function '}' ;	
	
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

helper : STRING ;
RANGES : '"<' INT '..' INT '>"' ;
STRING :  '"' (ESC | ~'"')* '"' ;
SYMBOL : ('_' | LETTER) (LETTER | DIGIT | '_' | '-')* ;
RANGE_SYMBOL : '<' INT '..' INT '>' ;

fragment ESC :   '\\' ["\\] ;

WS  :   [ \t\n\r]+ -> skip ;

SL_COMMENT
    :   '//' .*? '\n' -> skip
    ;
