#!/usr/bin/python

from SymbolTable import *

ttype = {}
arithm_ops = [ '+', '-', '*', '/', '%' ]
bit_ops = [ '|', '&', '^', '<<', '>>' ]
log_ops = [ '&&', '||' ]
comp_ops = [ '==', '!=', '>', '<', '<=', '>=' ]
ass_op = ['=']

for op in arithm_ops + bit_ops + log_ops + ass_op + comp_ops:
    ttype[op] = {}
    for type_ in ['int', 'float', 'string']:
        ttype[op][type_] = {}

for arithm_op in arithm_ops:
    ttype[arithm_op]['int']['int'] = 'int'
    ttype[arithm_op]['int']['float'] = 'float'
    ttype[arithm_op]['float']['int'] = 'float'
    ttype[arithm_op]['float']['float'] = 'float'
ttype['+']['string']['string'] = 'string'
ttype['*']['string']['int'] = 'string'
ttype['=']['float']['int'] = 'float'
ttype['=']['float']['float'] = 'float'
ttype['=']['int']['int'] = 'int'
ttype['=']['string']['string'] = 'string'

for op in bit_ops + log_ops:
    ttype[op]['int']['int'] = 'int'

for comp_op in comp_ops:
    ttype[comp_op]['int']['int'] = 'int'
    ttype[comp_op]['int']['float'] = 'int'
    ttype[comp_op]['float']['int'] = 'int'
    ttype[comp_op]['float']['float'] = 'int'
    ttype[comp_op]['string']['string'] = 'int'

class IncompatibleTypesError(Exception):
    pass

class DuplicatedSymbolError(Exception):
    pass

class SymbolNotDeclaredError(Exception):
    pass

class TypeChecker(object):

    def dispatch(self, node, *args):
        self.node = node
        className = node.__class__.__name__
        meth = getattr(self, 'visit_' + className)
        return meth(node, *args)
    
    def findVariable(self, tab, variable):
        #print "finding:", variable, "in:", tab.symbols
        if tab.symbols.has_key(variable):
            return tab.get(variable)
        elif tab.funargs.has_key(variable):
            return tab.funargs[variable]
        elif tab.name == variable:
            return tab
        elif tab.getParentScope() != None:
            return self.findVariable(tab.getParentScope(), variable)
        else:
            return None
        
    def findFunArg(self, tab, fun, position):
        #print "searching for", fun, position, "in", tab.symbols
        #print tab.symbol.name, fun
        if tab.name == fun:
            for funarg in tab.funargs:
                if tab.funargs[funarg].position == position:
                    #print "found as current tab name"
                    return tab.funargs[funarg]
        if tab.getParentScope() == None:
            #print "no parent scope"
            return None
        #print "searching for", fun, position, "in parent scope", tab.getParentScope().symbols
        if tab.getParentScope().symbols.has_key(fun):
            if tab.getParentScope().get(fun).name == fun:
                for funarg in tab.getParentScope().get(fun).funargs:
                    if tab.getParentScope().get(fun).funargs[funarg].position == position:
                        #print "found in parent scope"
                        return tab.getParentScope().get(fun).funargs[funarg]
        return self.findFunArg(tab.getParentScope(), fun, position)
    
    def getFunReturnType(self, tab):
        if tab == None:
            return None
        elif tab.name != None:
            return tab.type
        else:
            TypeChecker.getFunReturnType(self, tab.getParentScope())
    
    def getFunArgs(self, tab, fun):
        if tab.name == fun:
            return tab.funargs
        if tab.getParentScope() == None:
            return None
        if tab.getParentScope().symbols.has_key(fun):
            if tab.getParentScope().get(fun).name == fun:
                return tab.getParentScope().get(fun).funargs
        return self.getFunArgs(tab.getParentScope(), fun) 

    def visit_Program(self, node):
        tab = SymbolTable(None, "program", None)
        self.dispatch(node.declarations, tab)
        self.dispatch(node.fundefs, tab)
        self.dispatch(node.instructions, tab)

    def visit_Declarations(self, node, tab):
        for declaration in node.declarations:
            self.dispatch(declaration, tab)
            
    def visit_Declaration(self, node, tab):
        self.dispatch(node.inits, tab, node.type)

    def visit_Inits(self, node, tab, type):
        for init in node.inits:
            self.dispatch(init, tab, type)

    def visit_Init(self, node, tab, type):
        #print "init:", node.id, type
        errorOccured = False
        for symbol in tab.symbols:
            if symbol == node.id:
                print "line {1}: Duplicated usage of symbol {0}".format(node.id, node.line)
                errorOccured = True
                #raise DuplicatedSymbolError
        if not errorOccured:        
            tab.put(node.id, VariableSymbol(node.id, type, node.expression))
        #print "init:", tab.symbols
        

    def visit_Instructions(self, node, tab):
        for instruction in node.instructions:
            self.dispatch(instruction, tab)
 
    def visit_Instruction(self, node, tab):
        pass

    def visit_Print(self, node, tab):
        self.dispatch(node.expression, tab)

    def visit_Labeled(self, node, tab):
        self.dispatch(node.instruction, tab)
        
    def visit_Assignment(self, node, tab):
        #print "assignment:", node.id, tab.symbols
        variable = self.findVariable(tab, node.id)
        if variable == None:
            print "line {1}: Symbol {0} not defined before".format(node.id, node.line)
        else:
            valueType = self.dispatch(node.expression, tab)
            if valueType == None:
                return None
            if not ttype["="][variable.type].has_key(valueType):
                #print variable.name, variable.type
                print "line {3}: Value of type {0} cannot be assigned to symbol {1} of type {2}".format(valueType, node.id, variable.type, node.line)
            else:
                return ttype["="][variable.type][valueType]
        
    def visit_Choice(self, node, tab):
        self.dispatch(node._if, tab)
        self.dispatch(node._else, tab)

    def visit_If(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_Else(self, node, tab):
        self.dispatch(node.statement, tab)

    def visit_While(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_RepeatUntil(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_Return(self, node, tab):
        type = self.dispatch(node.expression, tab)
        ret_type = TypeChecker.getFunReturnType(self, tab)
        if ret_type == 'float' and type != 'int' and type != 'float':
            print "line {0}: Return type {1} incompatible with declared {2}".format(node.line, type, ret_type)
        elif ret_type == 'int' and type != 'int':
            print "line {0}: Return type {1} incompatible with declared {2}".format(node.line, type, ret_type)
        elif ret_type == 'string' and type != 'string':
            print "line {0}: Return type {1} incompatible with declared {2}".format(node.line, type, ret_type)

    def visit_Continue(self, node, tab):
        pass

    def visit_Break(self, node, tab):
        pass

    def visit_Compound(self, node, tab, *args):
        if len(args) > 0 and args[0] is True:
            self.dispatch(node.declarations, tab)
            self.dispatch(node.instructions, tab)
        else:
            new_tab = SymbolTable(tab, None, None)
            self.dispatch(node.declarations, new_tab)
            self.dispatch(node.instructions, new_tab)
        
    def visit_Condition(self, node, tab):
        pass
    
    def visit_Expression(self, node, tab):
        pass

    def visit_Const(self, node, tab):
        value = node.value
        if value[0] == '"' and value[len(value) - 1] == '"':
            type = 'string'
        else:
            try:
                int(value)
                type = 'int'
            except ValueError:
                try:
                    float(value)
                    type = 'float'
                except ValueError:
                    print "line {1}: Value's {0} type is not recognized".format(value, node.line)
        return type

    def visit_Id(self, node, tab):
        #print "ID:", node.id
        variable = self.findVariable(tab, node.id)
        if variable == None:
            print "line {1}: Symbol {0} not declared before".format(node.id, node.line)
        else:
            return variable.type

    def visit_BinExpr(self, node, tab):
        try:
            type1 = self.dispatch(node.expr1, tab)
            type2 = self.dispatch(node.expr2, tab)
            op = node.operator;
            type = ttype[op][type1][type2]
            #print type1, type2, op
            return type
        except KeyError:
            print "line {0}: Incompatible expression types".format(node.line)
            #raise IncompatibleTypesError
        except IncompatibleTypesError:
            pass
            #raise IncompatibleTypesError

    def visit_ExpressionInParentheses(self, node, tab):
        expression = node.expression
        type = self.dispatch(expression, tab)
        return type
    
    def visit_IdWithParentheses(self, node, tab):
        #print tab.symbols
        variable = self.findVariable(tab, node.id)
        #print variable.name, variable.type
        if variable == None:
            print "line {1}: Symbol {0} not declared before".format(node.id, node.line)
            return None
        if type(variable) is not SymbolTable:
            print "line {1}: {0} is not a function".format(node.id, node.line)
            return None
        #print "id with parentheses:", node.id, tab.symbols
        funcall_argtypes = self.dispatch(node.expression_list, tab)
        declared_fun_args = self.getFunArgs(tab, node.id)
        if len(funcall_argtypes) != len(declared_fun_args):
            print "line {3}: Function {0} takes {1} arguments, but {2} are supplied".format( \
                    node.id, len(declared_fun_args), len(funcall_argtypes), node.line)
            return None
        for argumentSymbol in declared_fun_args.values():
            corresponding_funcall_argtype = funcall_argtypes[argumentSymbol.position]
            if corresponding_funcall_argtype == None:
                continue
            if not ttype['='][argumentSymbol.type].has_key(corresponding_funcall_argtype):
                print "line {4}: Function {0}, argument {1}: cannot convert actual argument type " \
                        "({2}) to required type ({3})".format( \
                        node.id, argumentSymbol.position, \
                        corresponding_funcall_argtype, argumentSymbol.type, node.line)
        return variable.type

    def visit_ExpressionList(self, node, tab):
        expressions = node.expressions
        return map(lambda expression: self.dispatch(expression, tab), expressions)

    def visit_FunctionDefinitions(self, node, tab):
        for fundef in node.fundefs:
            self.dispatch(fundef, tab)

    def visit_FunctionDefinition(self, node, tab):
        new_tab = SymbolTable(tab, node.id, node.type)
        tab.put(node.id, new_tab)
        self.dispatch(node.arglist, new_tab)
        self.dispatch(node.compound_instr, new_tab, True)
    
    def visit_ArgumentList(self, node, tab):
        for arg in node.arg_list:
            self.dispatch(arg, tab, node.arg_list.index(arg))

    def visit_Argument(self, node, tab, position):
        #print "fun args:", node.id, node.type
        errorOccured = False
        for symbol in tab.symbols:
            if symbol == node.id:
                print "line {1}: Duplicated usage of symbol {0}".format(node.id, node.line)
                errorOccured = True
                #raise DuplicatedSymbolError
        if not errorOccured:
            #tab.put(node.id, VariableSymbol(node.id, node.type, None))
            tab.funargs[node.id] = ArgumentSymbol(node.id, node.type, position)
            return node.type
    
