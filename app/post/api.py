# encoding:utf-8
import time
from datetime import datetime
from flask import request
from . import post
from app.models import Post, Catagory
from app import db, app, picSet
from restful import *
import requests

@post.route('/')
@restful
def return_page_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.create_time.desc()).paginate(
        page, per_page=app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return [each.return_dict() for each in posts]

@post.route('/<post_id>', methods=['GET', 'DELETE'])
@restful
def return_one_post(post_id):
    """
    由post_id返回具体文章的内容
    """
    if request.method == 'GET':
        post = Post.query.filter_by(post_id=post_id).first()
        if not post:
            raise NotFoundError("no this post")
        return post.return_dict()
    elif request.method == 'DELETE':
        post = Post.query.filter_by(post_id=post_id).first()
        if not post:
            raise NotFoundError("no this post")
        # 删除文章对应的标签：
        all_catagory_list = Catagory.query.filter_by(post_id=post_id).all()
        for each in all_catagory_list:
            db.session.delete(each)
        db.session.delete(post)
        db.session.commit()
        return ''


@post.route('/return_all_posts')
@restful
def return_all_posts():
    all_posts_list = Post.query.order_by(Post.create_time.desc()).all()
    return [each.return_dict() for each in all_posts_list]

@post.route('/write', methods=['POST'])
@restful
def write_post_api():
    title = request.form.get('title')
    content = request.form.get('content')
    catagory = request.form.get('catagory')
    file = request.files.get('file')
    if not (title and content and catagory and file):
        raise BadRequestError("The request body is not present")
    post_id = int(time.time())
    filename = picSet.save(file, name='cover-{}'.format(post_id) + '.')
    cover_url = 'https://static.pushy.site/pics/{}'.format(filename)
    headers = {
        'Content-Type': 'text/plain'
    }
    body_html = requests.post("https://api.github.com/markdown/raw", content.encode('utf-8'), headers=headers).text
    new_post = Post(title=title, body=content, post_id=post_id, cover_url=cover_url, body_html=body_html)
    db.session.add(new_post)
    db.session.commit()
    # 将文章的标签存入Catagory模型的item字段中：
    for each in catagory.split(','):
        new_item = Catagory(item=each, post_id=post_id)
        db.session.add(new_item)
    db.session.commit()
    return new_post.return_dict()

@post.route('/update', methods=['POST'])
@restful
def update_post_api():
    title = request.json.get('title')
    content = request.json.get('content')
    post_id = request.json.get('post_id')
    if not (title and content and post_id):
        raise BadRequestError('The request body is not present')
    headers = {
        'Content-Type': 'text/plain'
    }
    body_html = requests.post("https://api.github.com/markdown/raw", content.encode('utf-8'), headers=headers).text
    post = Post.query.filter_by(post_id=post_id).first()
    post.title = title
    post.body = content
    post.body_html = body_html
    post.update_time = datetime.now()
    db.session.commit()
    return post.return_dict()


@post.route('/write/pic', methods=['POST'])
@restful
def upload_post_picture():
    for form_file in request.files.getlist('file'):
        picSet.save(form_file)
        return 'http://static.pushy.site/pic/' + form_file.filename

@post.route('/like', methods=['POST'])
@restful
def increase_post_like():
    post_id = request.json.get('post_id')
    pre = Post.query.filter_by(post_id=post_id).first()
    if not pre.good:
        pre.good = 1
    else:
        pre.good += 1
    db.session.commit()
    return {
        'good': pre.good
    }
