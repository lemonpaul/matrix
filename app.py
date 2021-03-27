import base64
import matplotlib
import networkx as nx
import matplotlib.pyplot as plt

from datetime import datetime
from flask import Flask, render_template, request, url_for, current_app, send_file
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from importlib import import_module
from io import BytesIO
from matplotlib.figure import Figure
from redis import Redis
from rq import Queue, Connection, Worker
from time import sleep


matplotlib.use('Agg')

server = Flask(__name__)

server.config.from_object('config')
config = server.config

redis_conn = Redis(host=config['REDIS_HOST'])
queue = Queue(connection=redis_conn)

db = SQLAlchemy(server)

bootstrap = Bootstrap(server)

managment_commands = Manager(server)


@server.route('/')
def index():
    return render_template('index.html', title='Home')


@server.route('/theory')
def theory():
    return render_template('theory.html', title='Theory')


@server.route('/matrix')
def matrix_index():
    from models import Matrix

    page = request.args.get('page', 1, type=int)
    matrices = Matrix.query.paginate(
        page, current_app.config['MATRICES_PER_PAGE'], False
    )
    next_url = url_for('matrix_index', page=matrices.next_num) \
        if matrices.has_next else None
    prev_url = url_for('matrix_index', page=matrices.prev_num) \
        if matrices.has_prev else None
    return render_template('matrix/index.html', title='Matrices', matrices=matrices.items,
                           page=matrices.page, pages=matrices.pages, per_page=matrices.per_page, \
                           total=matrices.total, next_url=next_url, prev_url=prev_url)


@server.route('/poset')
def poset():
    G = nx.complete_graph(5)
    nx.draw(G)

    img = BytesIO() # file-like object for the image
    plt.savefig(img, format='png') # save the image to the stream
    plt.clf()

    data = base64.b64encode(img.getbuffer()).decode("ascii")
    return render_template('poset.html', title='Partial order set of D-classes', data=data)


@server.route('/explore/<string:class_name>')
def explore_index(class_name):
    from models import D_class, intersection, height, width

    d_classes = D_class.query.all()
    return render_template('explore/index.html', title=class_name+'-classes',
                           d_classes=d_classes, intersection=intersection, 
                           class_name=class_name, height=height, width=width)


@server.route('/explore/<string:class_name>/<int:class_id>')
def explore_show(class_name, class_id):
    width = int(request.args.get('width'))
    height = int(request.args.get('height'))
    size = int(request.args.get('size'))

    model = getattr(import_module('models'), class_name+'_class')

    matrices = model.query.get(class_id).matrices

    return render_template('explore/show.html', matrices=matrices, width=width, height=height, \
                           size=size)


@server.route('/class/<string:class_name>/<int:class_id>')
def class_show(class_name, class_id):
    from models import Matrix

    model = getattr(import_module('models'), class_name+'_class')

    page = request.args.get('page', 1, type=int)
    matrices = db.session.query(Matrix).join(model).filter(model.id == class_id).paginate(
        page, current_app.config['MATRICES_PER_PAGE'], False
    )
    next_url = url_for('main.class_show', class_name=class_name, class_id=class_id, \
                       page=matrices.next_num) \
        if matrices.has_next else None
    prev_url = url_for('main.class_show', class_name=class_name, class_id=class_id, \
                       page=matrices.prev_num) \
        if matrices.has_prev else None

    return render_template('class/show.html', class_name=class_name, matrices=matrices.items,
                           page=matrices.page, pages=matrices.pages, per_page=matrices.per_page, \
                           total=matrices.total, next_url=next_url, prev_url=prev_url)


import utils
