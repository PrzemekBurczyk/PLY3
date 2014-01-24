
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
    
    def __init__(self):
        self.globalMemory = MemoryStack(Memory("global"))
        self.functionMemories = []

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
        self.globalMemory.put(node.id, node.expression.accept(self))    #dodajemy do obecnego memory w zakresie globalnym
    
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
        if len(self.functionMemories) == 0 or self.functionMemories[len(self.functionMemories) - 1].put_existing(node.id, node.expression.accept(self)) is False:
            self.globalMemory.put_existing(node.id, node.expression.accept(self))

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
        function = False
        if len(self.functionMemories) == 0:
            self.globalMemory.push(Memory("compound"))
        else:
            function = True
            self.functionMemories[len(self.functionMemories) - 1].push(Memory("compound"))
            
        node.declarations.accept(self)
        node.instructions.accept(self)
        
        if function is False:
            self.globalMemory.pop()
        else:
            self.functionMemories[len(self.functionMemories) - 1].pop()
    
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
        return node.id
    
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
        fundef = self.globalMemory.get(node.id.accept(self))
        functionMemory = Memory(node.id)
        map(lambda name, value: functionMemory.put(name, value), fundef.arglist.accept(self), node.expression_list.accept(self))
        self.functionMemories.append(functionMemory)
        try:
            fundef.accept(self)
            self.functionMemories.pop()
        except ReturnValueException as e:
            self.functionMemories.pop()
            return e.value
    
    @when(AST.ExpressionList)
    def visit(self, node):
        expressionResults = []
        for expression in node.expressions:
            expressionResults.append(expression.accept(self))
        return expressionResults
    
    @when(AST.FunctionDefinitions)
    def visit(self, node):
        for fundef in node.fundefs:
            self.globalMemory.put(fundef.id, fundef)
    
    @when(AST.FunctionDefinition)
    def visit(self, node):
        node.compound_instr.accept(self)
    
    @when(AST.ArgumentList)
    def visit(self, node):
        args = []
        for arg in node.arg_list:
            args.append(arg.accept(self))
        return args
    
    @when(AST.Argument)
    def visit(self, node):
        return node.id
