grammar Zysh;

top:   (functionDecl | varDecl)+ ;

varDecl
    :   '%define' meta SYNTAX ';'
    ;

functionDecl
    :   '%command' symbols (';' symbols)* '=' block
    ;	
	
symbols: sym+ '%' sym+ ;
sym: SYMBOL ;
meta: SYMBOL ;
block:  '{' privilege visibility function '}' ;	
	
privilege: '%privilege' INT	';' ;
visibility: '%visibility' INT ';' ;
function: '%function' SYMBOL ';' ;

DIGIT: [0-9] ;
INT :   [0-9]+ ;
	
fragment
LETTER : [a-zA-Z] ;

SYNTAX : STRING ;
HELP : STRING ;
STRING :  '"' (~'"')* '"' ;
SYMBOL: LETTER (LETTER | DIGIT | '_' | '-')* ;

WS  :   [ \t\n\r]+ -> skip ;

SL_COMMENT
    :   '//' .*? '\n' -> skip
    ;
