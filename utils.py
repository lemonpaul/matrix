import time

from app import managment_commands, db, queue, redis_conn, config
from models import Matrix, H_class, L_class, R_class, D_class

from rq import Connection, Worker


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
    from models import Matrix, L_class

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


@managment_commands.option('-h', '--height', dest='height', default=2)
@managment_commands.option('-w', '--width', dest='width', default=2)
@managment_commands.option('-t', '--threads', dest='n_threads', default=8)
def init(height, width, n_threads):
    height = int(height)
    width = int(width)
    n_threads = int(n_threads)

    clear_all()

    h_classes = []

    t_start = time.time()

    for h in range(1, height+1):
        for w in range(1, width+1):

            matrices = []

            print(f'Initialization {1 << w * h} {w}x{h} matrices...')

            for b in range(0, 1 << w * h):
                matrix = get_matrix(h, w, b)
                matrices.append(matrix)

                alchemy_matrix = Matrix(width=w, height=h, body=b)
                db.session.add(alchemy_matrix)

            print(f'Computing H-classes for {w}x{h} matrices...')

            if n_threads < 1 << w * h and n_threads > 1:
                n_matrices = 1 << w * h
                s_batch = int(n_matrices / n_threads)

                jobs = []
                for idx in range(n_threads):
                    matrix_from = s_batch * idx
                    matrix_to = min((idx + 1) * s_batch, n_matrices)
                    jobs.append(queue.enqueue(partial_h_class,
                                              matrices[matrix_from:matrix_to]))

                while any([job.result is None for job in jobs]):
                    continue

                size_h_classes = []
                for job in jobs:
                    size_h_classes.append(job.result)

                while len(size_h_classes) > 1:
                    jobs = []

                    for idx in range(0, len(size_h_classes), 2):
                        jobs.append(queue.enqueue(reduce_h_classes,
                                                  size_h_classes[idx],
                                                  size_h_classes[idx+1]))

                    while any([job.result is None for job in jobs]):
                        continue

                    reduced_h_classes = []
                    for job in jobs:
                        reduced_h_classes.append(job.result)

                    size_h_classes = reduced_h_classes

                size_h_classes = size_h_classes[0]

            else:
                size_h_classes = partial_h_class(matrices)

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

    print('Storing H-classes in database...')

    for h_class in h_classes:
        cls = H_class()
        for matrix in h_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.h_class = cls

    print('Storing L-classes in database...')

    for l_class in l_classes:
        cls = L_class()
        for matrix in l_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.l_class = cls

    print('Storing R-classes in database...')

    for r_class in r_classes:
        cls = R_class()
        for matrix in r_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.r_class = cls

    print('Storing D-classes in database...')

    for d_class in d_classes:
        cls = D_class()
        for matrix in d_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.d_class = cls

    db.session.commit()

    t_end = time.time()

    print(f'Estimated time: {t_end - t_start} s.')


@managment_commands.command
def build_orbits():
    print('Adjency matrix:')
    dim = D_class.query.count()
    adjency_matrix = []
    regular_classes = []
    d_classes = [[m.as_list() for m in d.matrices] for d in D_class.query.all()]
    for k in range(dim):
        adjency_matrix.append([])
        for l in range(dim):
            adjency_matrix[k].append(0)
    for idx_1, d_class_1 in enumerate(d_classes):
        if is_regular(d_class_1[0]):
            regular_classes.append(idx_1+1)
        for matrix in d_class_1:
            i_matrix = i(matrix)
            for idx_2, d_class_2 in enumerate(d_classes):
                if i_matrix in d_class_2:
                    adjency_matrix[idx_1][idx_2] = 1
        print(f'{idx_1+1},{",".join(str(i) for i in adjency_matrix[idx_1])}')
    print('Not regular classes:')
    print(",".join(str(i) for i in not_regular_classes()))
    print('Inverse classes:')
    print(",".join(str(i) for i in inverse_classes()))


@managment_commands.command
def runworker():
    with Connection(redis_conn):
        worker = Worker(config['QUEUES'])
        worker.work()
