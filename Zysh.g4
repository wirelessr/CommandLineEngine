grammar Zysh;

top:   (functionDecl | varDecl)+ ;

varDecl
    :   '%define' meta syntax helper ';'
    ;

functionDecl
    :   '%command' symbols (';' symbols)* '=' block
    ;	
	
symbols: sym+ '%' arg+ ;
sym: SYMBOL ;
meta: SYMBOL ;
arg: SYMBOL;
block:  '{' privilege visibility function '}' ;	
	
privilege: '%privilege' INT	';' ;
visibility: '%visibility' INT ';' ;
function: '%function' SYMBOL ';' ;

DIGIT: [0-9] ;
INT :   [0-9]+ ;
	
fragment
LETTER : [a-zA-Z] ;

syntax : STRING ;
helper : STRING ;
STRING :  '"' (~'"')* '"' ;
SYMBOL: LETTER (LETTER | DIGIT | '_' | '-')* ;

WS  :   [ \t\n\r]+ -> skip ;

SL_COMMENT
    :   '//' .*? '\n' -> skip
    ;
