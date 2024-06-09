import time

from app import db
from models import D_class, H_class, L_class, Matrix, R_class


def width(matrix):
    return len(matrix[0])


def height(matrix):
    return len(matrix)


def join(vector1, vector2):
    if len(vector1) != len(vector2):
        return None
    return [e1 | e2 for e1, e2 in zip(vector1, vector2)]


def meet(vector1, vector2):
    if len(vector1) != len(vector2):
        return None
    return [e1 & e2 for e1, e2 in zip(vector1, vector2)]


def transpose(matrix):
    width = len(matrix[0])

    transpose_matrix = [[]] * width
    for i in range(width):
        transpose_matrix[i] = [vector[i] for vector in matrix]

    return transpose_matrix


def complement(matrix):
    height = len(matrix)

    complement_matrix = [[]] * height
    for i in range(height):
        complement_matrix[i] = [int(not value) for value in matrix[i]]

    return complement_matrix


def space(matrix):
    space = set([tuple(vector) for vector in matrix])

    n = len(matrix)
    m = len(matrix[0])

    for i in range(n):
        for j in range(i+1, n):
            space.add(tuple(join(matrix[i], matrix[j])))

    space.add((0,) * m)

    return space


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


def comparable(vector1, vector2):
    if all(x <= y for x, y in zip(vector1, vector2)) or \
            all(x >= y for x, y in zip(vector1, vector2)):
        return True
    return False


def lattice(space_):
    n = len(space_)

    lattice_ = list()

    for i in range(n):
        lattice_.append(list())
        for j in range(n):
            if i == j:
                lattice_[i].append(1)
            elif comparable(space[i], space[j]):
                lattice_[i].append(1)
            else:
                lattice_[i].append(0)

    return lattice_


def isomorphic(lattice1, lattice2):
    unordered_degree_sequence1 = [sum(row) for row in lattice1]
    unordered_degree_sequence2 = [sum(row) for row in lattice2]
    if unordered_degree_sequence1[0] != unordered_degree_sequence2[0]:
        return False
    return sorted(unordered_degree_sequence1) == \
        sorted(unordered_degree_sequence2)


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
            result[i][j] = int(any(meet(v1, v2)))

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
            result[i][j] = int(all(join(v1, v2)))

    return result


def i(matrix):
    return disj_multiplication(
        complement(
            transpose(matrix)
        ),
        matrix
    )


def i_adjency_matrix():
    from models import D_class
    d_classes = [[matrix.as_list() for matrix in d_class.matrices]
                 for d_class in D_class.query]
    d_size = len(d_classes)

    adjency_matrix = [[]] * d_size
    for idx in range(d_size):
        adjency_matrix[idx] = [0] * d_size

        for matrix in d_classes[idx]:
            for d_class in filter(lambda d_class: i(matrix) in d_class,
                                  d_classes):
                adjency_matrix[idx][d_classes.index(d_class)] = 1

    return adjency_matrix


def intersection(l_class_id_1, l_class_id_2):
    from models import L_class, Matrix

    set_1 = {matrix.id for matrix in L_class.query.get(l_class_id_1).matrices}
    set_2 = {matrix.id for matrix in L_class.query.get(l_class_id_2).matrices}

    meet_set = set_1 & set_2

    return Matrix.query.filter(Matrix.id.in_(meet_set))


def is_idempotent(matrix):
    return len(matrix) == len(matrix[0]) and \
        conj_multiplication(matrix, matrix) == matrix


def is_primary_idempotent(matrix):
    return width(matrix) == height(matrix) and \
        conj_multiplication(matrix, matrix) == matrix and \
        i(matrix) != matrix


def is_secondary_idempotent(matrix):
    return width(matrix) == height(matrix) and \
        conj_multiplication(matrix, matrix) == matrix and \
        i(matrix) == matrix


def is_regular(a):
    from models import Matrix

    if height(a) != width(a):
        return False

    matrices = [matrix.as_list() for matrix in Matrix.query]

    matrices_x = filter(lambda m: width(m) == width(a) and
                        height(m) == height(a), matrices)

    for x in matrices_x:
        if conj_multiplication(conj_multiplication(a, x), a) == a:
            return True

    return False


def is_class_regular(cls):
    return is_regular(cls[0])


def not_regular_classes():
    from models import D_class
    d_classes = [[matrix.as_list() for matrix in d_class.matrices]
                 for d_class in D_class.query]
    d_size = len(d_classes)

    not_regular_classes = []

    for idx in range(d_size):
        if not is_class_regular(d_classes[idx]):
            not_regular_classes.append(idx+1)

    return not_regular_classes


def inverse_classes():
    from models import D_class

    d_size = D_class.query.count()

    inverse_classes = []

    for idx in range(1, d_size+1):
        inverse = True
        for r_cls in D_class.query.get(idx).r_classes():
            r_class = [matrix.as_list() for matrix in r_cls.matrices]
            if len(list(filter(lambda m: is_idempotent(m),  r_class))) != 1:
                inverse = False
                break
        for l_cls in D_class.query.get(idx).l_classes():
            l_class = [matrix.as_list() for matrix in l_cls.matrices]
            if len(list(filter(lambda m: is_idempotent(m),  l_class))) != 1:
                inverse = False
                break
        if inverse:
            inverse_classes.append(idx)

    return inverse_classes


def find_alchemy_matrix(matrix):
    from models import Matrix

    h = len(matrix)
    w = len(matrix[0])

    body = 0
    for i in range(h):
        for j in range(w):
            body |= ((1 & matrix[i][j]) << (h * w - (i * w + j) - 1))

    return Matrix.query.filter(Matrix.height == h, Matrix.width == w,
                               Matrix.body == body).first()


def get_matrix(height, width, body):
    data = [[]] * height
    for k in range(height):
        data[k] = [0] * width
    for i in range(height):
        for j in range(width):
            shift = width * height - (i * width + j) - 1
            if 1 << shift & body:
                data[i][j] = 1
    return data


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


def reduce_h_classes(h_classes_1, h_classes_2):
    s_h_class = len(h_classes_2)
    for h_class_1 in h_classes_1:
        matrix_1 = h_class_1[0]
        for idx in range(0, s_h_class):
            matrix_2 = h_classes_2[idx][0]
            if row_space(matrix_1) == row_space(matrix_2) and \
                    column_space(matrix_1) == column_space(matrix_2):
                h_classes_2[idx].extend(h_class_1)
                break
        else:
            h_classes_2.append(h_class_1)

    return h_classes_2


def clear_all():
    print('Clearing old data...')

    Matrix.query.delete()
    H_class.query.delete()
    L_class.query.delete()
    R_class.query.delete()
    D_class.query.delete()
    db.session.commit()
