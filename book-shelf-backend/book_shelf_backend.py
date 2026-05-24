from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
CORS(app)

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/bookshelf'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-123'

db = SQLAlchemy(app)

# ========== МОДЕЛИ ==========

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

class Publisher(db.Model):
    __tablename__ = 'publishers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    year = db.Column(db.Integer)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating_avg = db.Column(db.Float, default=0)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    publisher = db.relationship('Publisher', backref='books')
    genres = db.relationship('Genre', secondary='book_genres', backref=db.backref('books', lazy=True))

book_genres = db.Table('book_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    book = db.relationship('Book', backref='reviews')

# ========== API ЭНДПОИНТЫ ==========

@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        books = Book.query.all()
        result = []
        for book in books:
            genres_list = [genre.name for genre in book.genres] if book.genres else []
            result.append({
                'id': book.id,
                'title': book.title,
                'author': book.author or 'Неизвестен',
                'year': book.year,
                'price': book.price,
                'quantity': book.quantity,
                'description': book.description or '',
                'genres': genres_list,
                'rating_avg': float(book.rating_avg) if book.rating_avg else 0,
                'views_count': book.views_count or 0
            })
        return jsonify({'count': len(result), 'books': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404
        genres_list = [{'id': g.id, 'name': g.name} for g in book.genres] if book.genres else []
        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author or '',
            'year': book.year,
            'price': book.price,
            'quantity': book.quantity,
            'description': book.description or '',
            'rating_avg': float(book.rating_avg) if book.rating_avg else 0,
            'genres': genres_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books', methods=['POST'])
def create_book():
    try:
        data = request.get_json()
        if not data.get('title'):
            return jsonify({'error': 'Название книги обязательно'}), 400
        
        book = Book(
            title=data['title'],
            author=data.get('author', ''),
            year=data.get('year'),
            price=data.get('price', 0),
            quantity=data.get('quantity', 1),
            description=data.get('description', ''),
            user_id=data.get('user_id', 1)
        )
        db.session.add(book)
        db.session.commit()
        
        if data.get('genre_ids'):
            genres = Genre.query.filter(Genre.id.in_(data['genre_ids'])).all()
            book.genres.extend(genres)
            db.session.commit()
        
        return jsonify({'message': 'Книга создана', 'book': {'id': book.id, 'title': book.title}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404
        
        data = request.get_json()
        if 'title' in data: book.title = data['title']
        if 'author' in data: book.author = data['author']
        if 'year' in data: book.year = data['year']
        if 'price' in data: book.price = data['price']
        if 'quantity' in data: book.quantity = data['quantity']
        if 'description' in data: book.description = data['description']
        
        if 'genre_ids' in data:
            book.genres.clear()
            genres = Genre.query.filter(Genre.id.in_(data['genre_ids'])).all()
            book.genres.extend(genres)
        
        db.session.commit()
        return jsonify({'message': 'Книга обновлена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Удалить книгу"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404
        
        # Сохраняем название для сообщения
        book_title = book.title
        
        db.session.delete(book)
        db.session.commit()
        
        return jsonify({'message': f'Книга "{book_title}" успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка удаления: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<int:book_id>/reviews', methods=['GET'])
def get_reviews(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404
        reviews = Review.query.filter_by(book_id=book_id).all()
        result = [{'id': r.id, 'rating': r.rating, 'comment': r.comment, 'created_at': r.created_at.isoformat() if r.created_at else None} for r in reviews]
        return jsonify({
            'book_id': book_id,
            'book_title': book.title,
            'rating_avg': float(book.rating_avg) if book.rating_avg else 0,
            'reviews_count': len(result),
            'reviews': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<int:book_id>/reviews', methods=['POST'])
def add_review(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404
        data = request.get_json()
        review = Review(book_id=book_id, user_id=data.get('user_id', 1), rating=data['rating'], comment=data.get('comment', ''))
        db.session.add(review)
        avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.book_id == book_id).scalar()
        book.rating_avg = round(avg_rating, 2)
        db.session.commit()
        return jsonify({'message': 'Отзыв добавлен', 'rating_avg': float(book.rating_avg)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    try:
        genres = Genre.query.all()
        result = [{'id': g.id, 'name': g.name, 'description': g.description or ''} for g in genres]
        return jsonify({'genres': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/genre/<int:genre_id>', methods=['GET'])
def get_books_by_genre(genre_id):
    try:
        genre = Genre.query.get(genre_id)
        if not genre:
            return jsonify({'error': 'Жанр не найден'}), 404
        books = genre.books if genre.books else []
        result = [{'id': b.id, 'title': b.title, 'author': b.author, 'price': b.price} for b in books]
        return jsonify({'genre': genre.name, 'count': len(result), 'books': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = {
            'total_books': Book.query.count(),
            'total_users': User.query.count(),
            'total_reviews': Review.query.count(),
            'total_genres': Genre.query.count(),
            'total_publishers': Publisher.query.count(),
            'avg_price': float(db.session.query(func.avg(Book.price)).scalar() or 0),
            'total_quantity': int(db.session.query(func.sum(Book.quantity)).scalar() or 0),
            'total_views': int(db.session.query(func.sum(Book.views_count)).scalar() or 0)
        }
        return jsonify({'status': 'success', 'stats': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/init-db', methods=['GET'])
def init_database():
    try:
        db.create_all()
        return jsonify({'message': 'База данных готова'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("📚 BOOKSHELF API RUNNING")
    print("http://localhost:5000/api/books")
    print("=" * 50)
    app.run(debug=True, port=5000)