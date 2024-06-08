import itertools


def width(matrix):
    return len(matrix[0])


def height(matrix):
    return len(matrix)


def conj_multiplication(matrix1, matrix2):
    if len(matrix1[0]) != len(matrix2):
        return None

    n = len(matrix1)
    m = len(matrix2[0])

    result = list()
    for i in range(m):
        result.append([0] * n)

    for i in range(n):
        for j in range(m):
            v1 = matrix1[i]
            v2 = [v[j] for v in matrix2]
            result[i][j] = float(max(meet(v1, v2)))

    return result


def disj_multiplication(matrix1, matrix2):
    if len(matrix1[0]) != len(matrix2):
        return None

    n = len(matrix1)
    m = len(matrix2[0])

    result = list()
    for i in range(m):
        result.append([0] * n)

    for i in range(n):
        for j in range(m):
            v1 = matrix1[i]
            v2 = [v[j] for v in matrix2]
            result[i][j] = int(min(join(v1, v2)))

    return result


def is_regular(a, matrices):
    if height(a) != width(a):
        return False

    matrices_x = filter(lambda m: width(m) == width(a) and
                        height(m) == height(a), matrices)

    for x in matrices_x:
        if conj_multiplication(conj_multiplication(a, x), a) == a:
            return True

    return False


def is_secondary_idempotent(matrix):
    return width(matrix) == height(matrix) and \
        conj_multiplication(matrix, matrix) == matrix and \
        i(matrix) == matrix

def get_matrix(height, width, body):
    body = [int(sign) for sign in bin(body)[2:].zfill(height * width)]
    data = [[]] * height
    for k in range(height):
        data[k] = [0] * width
    for i in range(height):
        for j in range(width):
            data[i][j] = body[i*width+j]
    return data


def join(vector1, vector2):
    if len(vector1) != len(vector2):
        return None
    return [max(e1, e2) for e1, e2 in zip(vector1, vector2)]


def meet(vector1, vector2):
    if len(vector1) != len(vector2):
        return None
    return [min(e1, e2) for e1, e2 in zip(vector1, vector2)]


def space(matrix):
    space = set([tuple(vector) for vector in matrix])

    n = len(matrix)
    m = len(matrix[0])

    for i in range(n):
        for j in range(i+1, n):
            space.add(tuple(join(matrix[i], matrix[j])))

    space.add((0,) * m)

    return space


def transpose(matrix):
    width = len(matrix[0])

    transpose_matrix = [[]] * width
    for i in range(width):
        transpose_matrix[i] = [vector[i] for vector in matrix]

    return transpose_matrix


def column_space(matrix):
    transpose_matrix = transpose(matrix)
    return space(transpose_matrix)


def row_space(matrix):
    return space(matrix)


def h_equivalent(matrix1, matrix2):
    return row_space(matrix1) == row_space(matrix2) and \
        column_space(matrix1) == column_space(matrix2)


def l_equivalent(matrix1, matrix2):
    return row_space(matrix1) == row_space(matrix2)


def r_equivalent(matrix1, matrix2):
    return column_space(matrix1) == column_space(matrix2)


def as_set(data):
    return set(tuple(tuple(vector) for vector in matrix) for matrix in data)


def partial_h_class(matrices):
    h_classes = []

    for matrix in matrices:
        for h_class in h_classes:
            class_matrix = h_class[0]
            if h_equivalent(matrix, class_matrix):
                h_class.append(matrix)
                break
        else:
            h_class = [matrix]
            h_classes.append(h_class)

    return h_classes


def i(matrix):
    return disj_multiplication(
        complement(
            transpose(matrix)
        ),
        matrix
    )


def not_(a):
    if a == 0.5:
        return 0.5
    if a == 1:
        return 0
    if a == 0:
        return 1


def complement(matrix):
    height = len(matrix)

    complement_matrix = [[]] * height
    for i in range(height):
        complement_matrix[i] = [not_(value) for value in matrix[i]]

    return complement_matrix
