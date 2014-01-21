
import sys
import ply.yacc as yacc
from Cparser import Cparser
from TypeChecker_2 import TypeChecker
from Interpreter import Interpreter

if __name__ == '__main__':

    try:
        filename = sys.argv[1] if len(sys.argv) > 1 else "example.txt"
        file = open(filename, "r")
    except IOError:
        print("Cannot open {0} file".format(filename))
        sys.exit(0)

    Cparser = Cparser()
    parser = yacc.yacc(module=Cparser)
    text = file.read()
    ast = parser.parse(text, lexer=Cparser.scanner)
    if ast == None:
        sys.exit(-1)

    try:
        ast.printTree(0)
        TypeChecker().dispatch(ast)
        ast.accept(Interpreter())
    except Exception:
        print "Error while printing tree or performing type-check caused by previous syntax errors."
