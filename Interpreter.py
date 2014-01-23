
import AST
import SymbolTable
from Memory import *
from Exceptions import  *
from visit import *
from operator import *

operators = {}
operators['+'] = add
operators['-'] = sub
operators['*'] = mul
operators['/'] = div
operators['%'] = mod
operators['|'] = or_
operators['&'] = and_
operators['AND'] = and_
operators['OR'] = or_
operators['SHL'] = lshift
operators['SHR'] = rshift
operators['EQ'] = eq
operators['NEQ'] = ne
operators['>'] = lt
operators['<'] = gt
operators['LE'] = le
operators['GE'] = ge

class Interpreter(object):

    @on('node')
    def visit(self, node):
        pass
    
    @when(AST.Node)
    def visit(self, node):
        pass

    @when(AST.Program)
    def visit(self, node):
        node.declarations.accept(self)
        node.fundefs.accept(self)
        node.instructions.accept(self)
    
    @when(AST.Declarations)
    def visit(self, node):
        for declaration in node.declarations:
            declaration.accept(self)
    
    @when(AST.Declaration)
    def visit(self, node):
        node.inits.accept(self)
    
    @when(AST.Inits)
    def visit(self, node):
        for init in node.inits:
            init.accept(self)
    
    @when(AST.Init)
    def visit(self, node):
        #tu trzeba poczarowac z pamiecia
        pass
    
    @when(AST.Instructions)
    def visit(self, node):
        for instruction in node.instructions:
            instruction.accept(self)
    
    @when(AST.Instruction)
    def visit(self, node):
        pass
    
    @when(AST.Print)
    def visit(self, node):
        print node.expression.accept(self)
    
    @when(AST.Labeled)
    def visit(self, node):
        node.instruction.accept(self)
    
    @when(AST.Assignment)
    def visit(self, node):
        #poczarowac z pamiecia
        pass

    @when(AST.Choice)
    def visit(self, node):
        if not node._if.accept(self):
            node._else.accept(self) #return?
    
    @when(AST.If)
    def visit(self, node):
        if node.cond.accept(self):
            node.statement.accept(self)
            return True     #co z returnem powyzszego, czy potrzebny?
        else:
            return False
    
    @when(AST.Else)
    def visit(self, node):
        return node.statement.accept(self) #czy tu potrzebny return?
    
    @when(AST.While)
    def visit(self, node):
        r = None
        while node.cond.accept(self):
            try:
                r = node.statement.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue
        return r    #co tutaj daje return?
    
    @when(AST.RepeatUntil)
    def visit(self, node):
        r = None
        try:
            r = node.statement.accept(self)
        except BreakException:
            return r
        except ContinueException:
            pass
        while node.cond.accept(self):
            try:
                r = node.statement.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue
        return r
    
    @when(AST.Return)
    def visit(self, node):
        raise ReturnValueException(node.expression.accept(self))
    
    @when(AST.Continue)
    def visit(self, node):
        raise ContinueException()
    
    @when(AST.Break)
    def visit(self, node):
        raise BreakException()
    
    @when(AST.Compound)
    def visit(self, node):
        node.declarations.accept(self)
        node.instructions.accept(self)
    
    @when(AST.Condition)
    def visit(self, node):
        pass

    @when(AST.Expression)
    def visit(self, node):
        pass
    
    @when(AST.Const)
    def visit(self, node):
        return node.value
    
    @when(AST.Id)
    def visit(self, node):
        return node.id  #tu chyba trzeba zwrocic
    
    @when(AST.BinExpr)
    def visit(self, node):
        left = node.expr1.accept(self)
        right = node.expr2.accept(self)
        return operators[node.operator](left, right)
    
    @when(AST.ExpressionInParentheses)
    def visit(self, node):
        return node.expression.accept(self)
    
    @when(AST.IdWithParentheses)
    def visit(self, node):
        node.id.accept(self)
        node.expression_list.accept(self)
        #tu trzeba ogarnac wywolanie funkcji
    
    @when(AST.ExpressionList)
    def visit(self, node):
        for expression in node.expressions:
            expression.accept(self)
    
    @when(AST.FunctionDefinitions)
    def visit(self, node):
        for fundef in node.fundefs:
            fundef.accept(self)
    
    @when(AST.FunctionDefinition)
    def visit(self, node):
        node.arglist.accept(self)
        node.compound_instr.accept(self)
    
    @when(AST.ArgumentList)
    def visit(self, node):
        for arg in node.arg_list:
            arg.accept(self)
    
    @when(AST.Argument)
    def visit(self, node):
        type = node.type
        id = node.id
