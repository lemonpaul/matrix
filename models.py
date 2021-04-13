from sqlalchemy.orm import relationship

from app import db


def intersection(r_class, l_class):
    join = set(r_class.h_classes()) & set(l_class.h_classes())
    return list(join)[0]


def width(h_class):
    return h_class.matrices[0].width


def height(h_class):
    return h_class.matrices[0].height


class Matrix(db.Model):
    __tablename__ = 'matrix'
    id = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    body = db.Column(db.Integer)
    h_class_id = db.Column(db.Integer, db.ForeignKey('h_class.id'))
    h_class = relationship('H_class', back_populates='matrices')
    l_class_id = db.Column(db.Integer, db.ForeignKey('l_class.id'))
    l_class = relationship('L_class', back_populates='matrices')
    r_class_id = db.Column(db.Integer, db.ForeignKey('r_class.id'))
    r_class = relationship('R_class', back_populates='matrices')
    d_class_id = db.Column(db.Integer, db.ForeignKey('d_class.id'))
    d_class = relationship('D_class', back_populates='matrices')

    __mapper_args__ = {
        "order_by": id
    }

    def as_list(self):
        data = [[]] * self.height
        for k in range(self.height):
            data[k] = [0] * self.width
        for i in range(self.height):
            for j in range(self.width):
                shift = self.width * self.height - (i * self.width + j) - 1
                if 1 << shift & self.body:
                    data[i][j] = 1
        return data

    def __repr__(self):
        return '<Matrix {}x{}>'.format(self.width, self.height)


class H_class(db.Model):
    __tablename__ = 'h_class'
    id = db.Column(db.Integer, primary_key=True)
    matrices = relationship('Matrix', back_populates='h_class')

    __mapper_args__ = {
        "order_by": id
    }


class L_class(db.Model):
    __tablename__ = 'l_class'
    id = db.Column(db.Integer, primary_key=True)
    matrices = relationship('Matrix', back_populates='l_class')

    __mapper_args__ = {
        "order_by": id
    }

    def h_classes(self):
        return H_class.query.join(Matrix).join(L_class).filter_by(id=self.id).all()


class R_class(db.Model):
    __tablename__ = 'r_class'
    id = db.Column(db.Integer, primary_key=True)
    matrices = relationship('Matrix', back_populates='r_class')

    __mapper_args__ = {
        "order_by": id
    }

    def h_classes(self):
        return H_class.query.join(Matrix).join(R_class).filter_by(id=self.id).all()


class D_class(db.Model):
    __tablename__ = 'd_class'
    id = db.Column(db.Integer, primary_key=True)
    matrices = relationship('Matrix', back_populates='d_class')

    __mapper_args__ = {
        "order_by": id
    }

    def h_classes(self):
        return H_class.query.join(Matrix).join(D_class).filter_by(id=self.id).all()

    def l_classes(self):
        return L_class.query.join(Matrix).join(D_class).filter_by(id=self.id).all()

    def r_classes(self):
        return R_class.query.join(Matrix).join(D_class).filter_by(id=self.id).all()

