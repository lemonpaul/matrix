import time

from app import managment_commands, db, queue, redis_conn, config
from models import Matrix, H_class, L_class, R_class, D_class

from rq import Connection, Worker
from rq.registry import StartedJobRegistry

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
    return sorted(unordered_degree_sequence1) == sorted(unordered_degree_sequence2)


def multiplication(matrix1, matrix2):
    if len(matrix1[0]) != len(matrix2):
        return None

    n = len(matrix1)
    m = len(matrix2[1])

    result = list()
    for i in range(m):
        result.append([0] * n)

    for i in range(n):
        for j in range(m):
            v1 = matrix1[i]
            v2 = [v[j] for v in matrix2]
            result[i][j] = int(any(meet(v1, v2)))

    return result


def intersection(l_class_id_1, l_class_id_2):
    from models import Matrix, L_class

    set_1 = {matrix.id for matrix in L_class.query.get(l_class_id_1).matrices}
    set_2 = {matrix.id for matrix in L_class.query.get(l_class_id_2).matrices}

    meet_set = set_1 & set_2

    return Matrix.query.filter(Matrix.id.in_(meet_set))


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
            if row_space(matrix) == row_space(class_matrix) and \
                    column_space(matrix) == column_space(class_matrix):
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


def test(a, b):
    return a + b


def clear_all():
    print(f'Clearing old data...')

    Matrix.query.delete()
    H_class.query.delete()
    L_class.query.delete()
    R_class.query.delete()
    D_class.query.delete()
    db.session.commit()


def summ(a, b):
    a = a + b
    return a


@managment_commands.option('-h', '--height', dest='height', default=2)
@managment_commands.option('-w', '--width', dest='width', default=2)
@managment_commands.option('-t', '--threads', dest='n_threads', default=8)
def init(height, width, n_threads):
    registry = StartedJobRegistry(queue=queue)

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

            for b in range (0, 1 << w * h):
                matrix = get_matrix(h, w, b)
                matrices.append(matrix)

                alchemy_matrix = Matrix(width=w, height=h, body=b)
                db.session.add(alchemy_matrix)
            
            print(f'Computing H-classes for {w}x{h} matrices...')

            if n_threads < 1 << w * h and n_threads > 1:
                # array = [1, 2, 3, 4, 5, 6, 7, 8]

                # while len(array) > 1:
                #     jobs = []

                #     for idx in range(0, len(array), 2):
                #          print(f'Job {idx} received {array[idx]} and {array[idx+1]}.')
                #          jobs.append(queue.enqueue(test, array[idx], array[idx+1]))

                #     while len(queue) or registry.count:
                #         continue
                #     else:
                #         time.sleep(0.1)

                #     reduced_array = []
                #     for job in jobs:
                #         print(f'Job {jobs.index(job)} returned {job.result}.')
                #         reduced_array.append(job.result)
                #     
                #     array = reduced_array
                        
                n_matrices = 1 << w * h
                s_batch = int(n_matrices / n_threads)

                jobs = []
                for idx in range(n_threads):
                    matrix_from = s_batch * idx
                    matrix_to = min((idx + 1) * s_batch, n_matrices)
                    jobs.append(queue.enqueue(partial_h_class, matrices[matrix_from:matrix_to]))

                while len(queue) or registry.count:
                    continue
                else:
                    time.sleep(0.1)

                size_h_classes = []
                for job in jobs:
                    size_h_classes.append(job.result)
                
                while len(size_h_classes) > 1:
                    jobs = []

                    for idx in range(0, len(size_h_classes), 2):
                        jobs.append(queue.enqueue(reduce_h_classes, size_h_classes[idx], \
                                                  size_h_classes[idx+1]))
                        print(f'Job {idx} received {size_h_classes[idx]} and '
                              f'{size_h_classes[idx+1]}.')

                    while len(queue) or registry.count:
                        continue
                    else:
                        time.sleep(0.1)

                    reduced_h_classes = []
                    for job in jobs:
                        reduced_h_classes.append(job.result)
                        print(f'Job {jobs.index(job)} returned {job.result}')
                        
                    
                    size_h_classes = reduced_h_classes
                    
                size_h_classes = size_h_classes[0]
               
            else:
                size_h_classes = partial_h_class(matrices)
               
            h_classes.extend(size_h_classes)

    print(f'Computing L-classes...')

    l_classes = []

    for h_class in h_classes:
        matrix = h_class[0]

        for l_class in l_classes:
            class_matrix = l_class[0]
            if row_space(matrix) == row_space(class_matrix):
                l_class.extend(h_class)
                break
        else:
            l_class = []
            l_class.extend(h_class)
            l_classes.append(l_class)

    print(f'Computing R-classes...')

    r_classes = []

    for h_class in h_classes:
        matrix = h_class[0]

        for r_class in r_classes:
            class_matrix = r_class[0]
            if column_space(matrix) == column_space(class_matrix):
                r_class.extend(h_class)
                break
        else:
            r_class = []
            r_class.extend(h_class)
            r_classes.append(r_class)

    print(f'Computing D-classes...')

    d_classes = []

    for l_class in l_classes:
        matrix = l_class[0]
        for d_class in d_classes:
            class_matrix = d_class[0]

            r_class = next(filter(lambda r_class: class_matrix in r_class, r_classes))

            if as_set(l_class) & as_set(r_class):
                d_class.extend(l_class)
                break
        else:
            d_class = []
            d_class.extend(l_class)
            d_classes.append(d_class)
    
    print(f'Storing H-classes in database...')

    for h_class in h_classes:
        cls = H_class()
        for matrix in h_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.h_class = cls

    print(f'Storing L-classes in database...')

    for l_class in l_classes:
        cls = L_class()
        for matrix in l_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.l_class = cls

    print(f'Storing R-classes in database...')

    for r_class in r_classes:
        cls = R_class()
        for matrix in r_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.r_class = cls

    print(f'Storing D-classes in database...')

    for d_class in d_classes:
        cls = D_class()
        for matrix in d_class:
            mtx = find_alchemy_matrix(matrix)
            mtx.d_class = cls

    db.session.commit()

    t_end = time.time()
    
    print(f'Estimated time: {t_end - t_start} s.')


@managment_commands.command
def runworker():
    with Connection(redis_conn):
        worker = Worker(config['QUEUES'])
        worker.work()
