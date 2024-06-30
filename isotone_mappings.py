#!/bin/python

def as_mapping(matrix):
    function = []
    for i in range(len(matrix[0])):
        for j in range(len(matrix)):
            if matrix[i][j] == 1:
                function.append((i+1, j+1))

    return function
            
def get_functions(dimension: int):
    for index in range(2 ** (dimension * dimension)):
        raw = [int(el) for el in bin(index)[2:].zfill(dimension ** 2)]
        matrix = [raw[i*dimension:i*dimension+dimension] for i in range(dimension)]
        yield as_mapping(matrix)

if __name__ == "__main__":
    for function in get_functions(3):
        print(function)
