#!/usr/bin/env python
# coding=utf-8
import time

from app import db, managment_commands
from models import D_class, H_class, L_class, Matrix, R_class
from utils import (as_set, clear_all, find_sqla_matrix, get_matrix, i,
                   inverse_classes, is_regular, l_equivalent,
                   not_regular_classes, partial_h_class, r_equivalent)


@managment_commands.option('-h', '--height', dest='height', default=3)
@managment_commands.option('-w', '--width', dest='width', default=3)
def init(height: int, width: int):
    """
    Вычислить и сохранить в БД классы Грина для полугруппы матриц максимальной
    ширины width и высоты height.

    height:
        Максимальная высота матриц.

    width:
        Максимальная ширина матриц.
    """
    height = int(height)
    width = int(width)

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
            mtx = find_sqla_matrix(matrix)
            mtx.h_class = cls

    print('Storing L-classes in database...')

    for l_class in l_classes:
        cls = L_class()
        for matrix in l_class:
            mtx = find_sqla_matrix(matrix)
            mtx.l_class = cls

    print('Storing R-classes in database...')

    for r_class in r_classes:
        cls = R_class()
        for matrix in r_class:
            mtx = find_sqla_matrix(matrix)
            mtx.r_class = cls

    print('Storing D-classes in database...')

    for d_class in d_classes:
        cls = D_class()
        for matrix in d_class:
            mtx = find_sqla_matrix(matrix)
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
        print(f'{",".join(str(i) for i in adjency_matrix[idx_1])}')
    print('Not regular classes:')
    print(",".join(str(i) for i in not_regular_classes()))
    print('Inverse classes:')
    print(",".join(str(i) for i in inverse_classes()))

if __name__ == "__main__":
    managment_commands.run()
