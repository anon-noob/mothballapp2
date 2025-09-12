import numpy as np
from scipy.optimize import minimize
from ExprEval import evaluate
from Enums import OptimizeCellAxis

class Optimizer:
    def __init__(self):
        self.init = 0.3169516
        self.n = 12

        self.variables = {}
        
        self.imux = np.array([0.546, 0.546] + [0.91]*10)
        self.imuz = np.array([0.546, 0.546] + [0.91]*10)
        self.mmu  = np.array([0.31, 0.3274] + [0.026]*10)


        self.constraints: list[list[str], list[dict]] = [[],[]] # list[names, constraints]

    def setupVars(self, extraVars: dict):
        for k,v in extraVars.items():
            try:
                extraVars[k] = evaluate(v)
            except:
                extraVars[k] = 0
        self.variables = {'px': 0.0625} | extraVars
        self.n = int(self.variables.get('num_ticks',12))
    
    def setupConstants(self, imux, imuz, mmu):
        self.imux = np.array([evaluate(a, self.variables) for a in imux], dtype=float)
        self.imuz = np.array([evaluate(a, self.variables) for a in imuz], dtype=float)
        self.mmu = np.array([evaluate(a, self.variables) for a in mmu], dtype=float)

    def setupConstraints(self, iterable):
        c = []
        names = []
        for i, j in enumerate(iterable, 1):
            active, name, mode, t1, op, t2, comparison, num = j
            if active == "no":
                continue
            if not t1 and not t2:
                continue
            try: t1 = int(evaluate(t1, self.variables))
            except Exception as e:
                t1 = None
            try: t2 = int(evaluate(t2, self.variables))
            except Exception as e:
                t2 = None
            if t1 is None and t2 is None:
                continue
            if t2 is None and t1 is not None:
                t1, t2 = t2, t1
            if not name:
                name = f"Constraint {i}"
            names.append(name)
            
            num = evaluate(num, self.variables)
            # print("MODE", mode)
            if mode == 'F':
                num = num % 360
                if num > 180:
                    num = num - 360
                num*= np.pi/180
                if comparison== ">" or comparison == ">=":
                    if op == "-":
                        if t2:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: F[t1] - F[t2] - num)()})
                        else:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, num=num: lambda F: F[t1] - num)()})
                    elif op == "+":
                        if t2:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: F[t1] + F[t2] - num)()})
                        else:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, num=num: lambda F: F[t1] - num)()})
                elif comparison == "=":
                    if op == '-':
                        if t2:
                            c.append({'type': 'eq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: F[t1] - F[t2] - num)()})
                        else:
                            c.append({'type': 'eq', 'fun': (lambda t1=t1, num=num: lambda F: F[t1] - num)()})
                    elif op == "+":
                        if t2:
                            c.append({'type': 'eq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: F[t1] + F[t2] - num)()})
                        else:
                            c.append({'type': 'eq', 'fun': (lambda t1=t1, num=num: lambda F: F[t1] - num)()})
                else:
                    if op == "-":
                        if t2:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: -func(F, t1) + func(F, t2) + num)()})
                        else:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, num=num: lambda F: -func(F, t1) + num)()})
                    elif op == "+":
                        if t2:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, t2=t2, num=num: lambda F: -F[t1] - F[t2] + num)()})
                        else:
                            c.append({'type': 'ineq', 'fun': (lambda t1=t1, num=num: lambda F: -F[t1] + num)()})

                continue

            if mode == 'X':
                func = self.X
            elif mode == 'Z':
                func = self.Z

            if comparison== ">" or comparison == ">=":
                if op == "-":
                    if t2:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: func(F, t1) - func(F, t2) - num)(func)})
                    else:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, num=num: lambda F: func(F, t1) - num)(func)})
                elif op == "+":
                    if t2:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: func(F, t1) + func(F, t2) - num)(func)})
                    else:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, num=num: lambda F: func(F, t1) - num)(func)})
            elif comparison == "=":
                if op == '-':
                    if t2:
                        c.append({'type': 'eq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: func(F, t1) - func(F, t2) - num)(func)})
                    else:
                        c.append({'type': 'eq', 'fun': (lambda func, t1=t1, num=num: lambda F: func(F, t1) - num)(func)})
                elif op == "+":
                    if t2:
                        c.append({'type': 'eq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: func(F, t1) + func(F, t2) - num)(func)})
                    else:
                        c.append({'type': 'eq', 'fun': (lambda func, t1=t1, num=num: lambda F: func(F, t1) - num)(func)})
            else:
                if op == "-":
                    if t2:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: -func(F, t1) + func(F, t2) + num)(func)})
                    else:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, num=num: lambda F: -func(F, t1) + num)(func)})
                elif op == "+":
                    if t2:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, t2=t2, num=num: lambda F: -func(F, t1) - func(F, t2) + num)(func)})
                    else:
                        c.append({'type': 'ineq', 'fun': (lambda func, t1=t1, num=num: lambda F: -func(F, t1) + num)(func)})


        self.constraints = [names, c]

    def X(self, F, t):
        if t <= 0:
            return 0.0
        s = 0.0
        for i in range(1, t+1):
            inner = 0.0
            for j in range(i, t+1):
                inner += np.prod(self.imux[i-1:j-1])
            s += self.mmu[i-1] * np.sin(F[i-1]) * inner
        return s
    
    def Z(self, F, t):
        if t <= 0:
            return 0.0
        s = 0.0
        for i in range(1, t+1):
            inner = 0.0
            for j in range(i, t+1):
                inner += np.prod(self.imuz[i-1:j-1])
            s += self.mmu[i-1] * np.cos(F[i-1]) * inner
        return s

    def objectiveX(self, F):
        return self.X(F, self.n)
    
    def objectiveZ(self, F):
        return self.Z(F, self.n)
    
    def objectiveNegX(self, F):
        return -self.X(F, self.n)
    
    def objectiveNegZ(self, F):
        return -self.Z(F, self.n)

    def optimize(self, axis_to_optimize: OptimizeCellAxis, max_or_min: str):
        x0 = np.zeros(self.n, dtype=float)
        
        if axis_to_optimize == OptimizeCellAxis.X:
            if max_or_min == 'min':
                func = self.objectiveX
            elif max_or_min == 'max':
                func = self.objectiveNegX
        elif axis_to_optimize == OptimizeCellAxis.Z:
            if max_or_min == 'min':
                func = self.objectiveZ
            elif max_or_min == 'max':
                func = self.objectiveNegZ
        else:
            return ("Something went wrong!", 'function was invalid. Report this bug.', '')    

        res = minimize(func, x0, method='SLSQP', constraints=self.constraints[1], bounds=None, options={'maxiter': 500, 'ftol': 1e-12})
        self.F_opt = res.x
        self.res = res
        m = [c['fun'](self.F_opt) for c in self.constraints[1]]
        return (res, (self.constraints[0], m)) # (res, (constraintnames, constraintvalues))

    def postprocess(self):
        fopt = self.F_opt.copy()
        points = [[self.X(fopt, t) - self.X(fopt, 0),  self.Z(fopt, t) - self.Z(fopt, 0)] for t in range(0, self.n+1) ]
        fopt_deg = fopt * 180.0 / np.pi
        fopt2 = np.round(1000.0 * (np.mod(fopt_deg + 180.0, 360.0) - 180.0)) * 0.001
        diffs = np.diff(fopt2)
        
        x = [i[0] for i in points]
        y = [j[1] for j in points]

        return {
            'points': points,
            'fopt_deg': fopt_deg,
            'fopt2': fopt2,
            'diffs': diffs
        }

# if __name__ == "__main__":
#     a = Optimizer()
#     a.setupVars({})
#     def c1(F):
#         return a.X(F, 2) - 0.4375
#     def c2(F):
#         return a.X(F, 8) - 0.4375
#     def c3(F):
#         return a.Z(F, 8) - a.Z(F, 1) - 1.6
#     a.constraints = [['x1','x2','z'], [{'type': 'ineq', 'fun': c1}, {'type': 'ineq', 'fun': c2}, {'type': 'ineq', 'fun': c3}]]
#     a.optimize()