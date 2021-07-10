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


height_ = 2
width_ = 2

matrices = []
h_classes = []

for h in range(1, height_+1):
    for w in range(1, width_+1):
        size_matrices = []
        print(f'Initialization {w}x{h} matrices...')
        
        tuples_args = ([0, 0.5, 1], ) * (w * h)
        tuples = list(itertools.product(*tuples_args))
        
        for t in tuples:
            matrix = get_matrix(h, w, t)
            size_matrices.append(matrix)

        matrices.extend(size_matrices)

        print(f'Computing H-classes for {w}x{h} matrices...')
        
        size_h_classes = partial_h_class(size_matrices)

        h_classes.extend(size_h_classes)

print('Computing L-classes...')

l_classes = []

for h_class in h_classes:
    matrix = h_class[0]

    for l_class in l_classes:
        class_matrix = l_class[0]
        if l_equivalent(matrix, class_matrix):
            l_class.extend(h_class)
            break
    else:
        l_class = []
        l_class.extend(h_class)
        l_classes.append(l_class)

print('Computing R-classes...')

r_classes = []

for h_class in h_classes:
    matrix = h_class[0]

    for r_class in r_classes:
        class_matrix = r_class[0]
        if r_equivalent(matrix, class_matrix):
            r_class.extend(h_class)
            break
    else:
        r_class = []
        r_class.extend(h_class)
        r_classes.append(r_class)

print('Computing D-classes...')

d_classes = []

for l_class in l_classes:
    matrix = l_class[0]
    for d_class in d_classes:
        class_matrix = d_class[0]

        r_class = next(
            filter(lambda r_class: class_matrix in r_class, r_classes)
        )

        if as_set(l_class) & as_set(r_class):
            d_class.extend(l_class)
            break
    else:
        d_class = []
        d_class.extend(l_class)
        d_classes.append(d_class)

d_class = d_classes[17]

