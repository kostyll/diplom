# -*- coding: utf8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from random import randrange

import code_cleanup, re, math, functioner

operators = ["+-", "&=", "^=", "|=", "/=", "<<=", "%=", "*=", ">>=",
             "-=", "&&", "||", ",", "/", "%", "*", ".", "->",
             "--", "++", "==", ">=", ">", "<=", "!=", "<<", ">>", "!", "~",
             "sizeof", "+", "-", "=", "<", "&", "^", "|", "size_t", "?"]

function_regex = r"([A-Za-z_][0-9A-Za-z_]*\s*\()"

operand_regex = r"([^:\s;\(\)\{\}\[\]]+)"

key_words = ["int", "float", "long", "signed", "unsigned", "double", "char", "short", "break", "return", "void", "else"]

#https://github.com/morpheby/msisvit-lab-c-metrics
class Holsted:

    total_operators_count = 0
    unique_operators_count = 0
    total_operands_count = 0
    unique_operands_count = 0
    cleaned_code = ""
    text = ""

    def __init__(self, code):
        self.text = code
        cleaned_code = code_cleanup.cleanup_sharp(code)
        cleaned_code = code_cleanup.cleanup_comments(cleaned_code)
        (cleaned_code, total_string_count, unique_string_count) = code_cleanup.cleanup_and_get_strings_count(cleaned_code)
        self.total_operands_count += total_string_count
        self.unique_operands_count += unique_string_count
        self.cleaned_code = cleaned_code

    def get_all_operators(self):
        unique_operators = set()
        total_operators = 0

        for operator in operators:
            operators_count = self.cleaned_code.count(operator)
            if operators_count > 0:
                self.cleaned_code = self.cleaned_code.replace(operator, " ")
                total_operators += operators_count
                unique_operators.add(operator)
        self.total_operators_count += total_operators
        self.unique_operators_count += len(unique_operators)

        unique_functions = set()
        count = len(re.findall(function_regex, self.cleaned_code))
        cleanup_code = re.sub(function_regex, lambda match: [unique_functions.add(match.group(0)), " "][0], self.cleaned_code)
        self.cleaned_code = cleanup_code
        self.total_operators_count += count
        self.unique_operators_count += len(unique_functions)

    def get_all_operands(self):
        for key in key_words:
            self.cleaned_code = self.cleaned_code.replace(key, " ")

        operands = re.findall(operand_regex, self.cleaned_code)
        self.total_operands_count = len(operands)
        self.unique_operands_count = len(set(operands))

    def get_theoretical_program_dictionary(self):
        functions = functioner.get_function_declaration(self.text)
        n1s = 0
        n2s = 0
        for func in functions:
            n2s += len(func[2].split(","))
        n1s = len(functions)
        return n1s, n2s

    def run(self,func=True):
        if func==True:
            print = lambda *args,**kwargs: None
        result = {}
        self.get_all_operators()
        self.get_all_operands()

        n1 = self.unique_operators_count
        result.update({'n1_uniq_operatorts_count':n1})
        n2 = self.unique_operands_count
        result.update({'n1_uniq_operands_count':n2})
        N1 = self.total_operators_count
        result.update({'N1_total_operators_count':N1})
        N2 = self.total_operands_count
        result.update({'N2_total_operands_count':N2})

        print(u"Общее число операторов (N1): ", self.total_operators_count)
        print(u"Число уникальных операторов (n1): ", self.unique_operators_count)
        print(u"Общее число операндов (N2): ", self.total_operands_count)
        print(u"Число уникальных операндов (n2): ", self.unique_operands_count)

        n = self.unique_operators_count + self.unique_operands_count
        result.update({'n_alphabet':n})
        print(u"Алфавит (n): ", n)

        Ne = self.total_operators_count + self.total_operands_count
        result.update({'Ne_experimental_prgr_length':Ne})
        print(u"Экспериментальна длина программы (Nэ): ", Ne)
        Nt = n1 * math.log(n1, 2) + n2 * math.log(n2, 2)
        result.update({'Nt_teoretical_prgr_length':Nt})
        print(u"Теоретическая длина программы (Nт): ", Nt)


        V = Ne * math.log(n, 2)
        result.update({'V':V})
        print(u"Объем программы (V): ", V)

        n1s, n2s = self.get_theoretical_program_dictionary()

        Vs = Nt * math.log(n1s + n2s, 2)
        result.update({'V_potentional':Vs})
        print(u"Потенциальный oбъем (V*): ", Vs)

        L = Vs / V
        result.update({'L_prgr_level':L})
        print(u"Уровень программы (L): ", L)

        S = 1 / L
        result.update({'S_difficaltcy':S})
        print(u"Сложность программы (S): ", S)

        try:
            Ls = (2 / n2)*(n2 / N2)
            result.update({'Ls_prgr_level_expecticy':Ls})
            print(u"Ожидание уровня программы (L'): ", Ls)
        except:
            pass


        try:
            D = 1 / Ls
            result.update({'D_coding_difficalcy':D})
            print("Трудоемкость кодирования программы (D): ", D)
        except:
            pass

        try:
            I = V / D
            result.update({'I_inteligence':I})
            print(u"Интеллект программы (I): ", I)  
        except:
            pass

        E = Nt * math.log(n/L, 2)
        result.update({'E_inteligence_try_level':E})
        print(u"Оценка необходимых интеллектуальных усилий при разработке (E): ", E)

        return result


# {
#     u'n1_uniq_operands_count': 27, 
#     u'V_potentional': 1172.3107299919077, 
#     u'Ne_experimental_prgr_length': 159, 
#     u'Nt_teoretical_prgr_length': 307.9068681514875, 
#     u'L_prgr_level': 1.2382902871721972, 
#     u'n_alphabet': 62, 
#     u'N2_total_operands_count': 66, 
#     u'E_inteligence_try_level': 1738.3949912466576, 
#     u'S_difficaltcy': 0.8075650841804104, 
#     u'V': 946.7172133515132, 
#     u'n1_uniq_operatorts_count': 35, 
#     u'Ls_prgr_level_expecticy': 0, 
#     u'N1_total_operators_count': 93
#     }

def get_holsted(source, ast):

    #
    try:
        result_holsted =  Holsted(source).run()
        result = {}
        result.update({
                'V': result_holsted['V'],
                'n1': result_holsted['n_alphabet'],
                'N': result_holsted['Ne_experimental_prgr_length']

            })
        for key in result.keys():
            result[key] = round(result[key],2)
    except:
        return (-1,-1,-1)
    return result.values()
    # return (randrange(3,20),randrange(0,5)*randrange(1,20),randrange(2,11)*randrange(0,7))

__author__ = 'andrew.vasyltsiv'# -*- coding: utf8 -*-

