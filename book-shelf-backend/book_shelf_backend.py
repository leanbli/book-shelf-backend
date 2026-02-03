from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import psycopg2
 #комм leanbli сидорова варвара
app = Flask(__name__)
CORS(app)

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ POSTGRES ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/bookshelf_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-123'

db = SQLAlchemy(app)

# ========== МОДЕЛИ БАЗЫ ДАННЫХ ==========

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    year = db.Column(db.Integer)
    price = db.Column(db.Float) 
    quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='books')

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ (УПРОЩЕННАЯ) ==========

@app.route('/api/init-db', methods=['GET'])
def init_database():
    """Создание таблиц и тестовых данных"""
    try:
        print("🔧 Начинаем инициализацию базы данных...")
        
        with app.app_context():
            db.create_all()
            print("✅ Таблицы созданы")
            
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Тестовый пользователь создан (admin/admin123)")
            
            if Book.query.count() == 0:
                books = [
                    Book(title='Война и мир', author='Лев Толстой', year=1869, price=500.00, user_id=1, description='Роман-эпопея'),
                    Book(title='1984', author='Джордж Оруэлл', year=1949, price=300.50, user_id=1, description='Антиутопия'),
                    Book(title='Мастер и Маргарита', author='Михаил Булгаков', year=1967, price=450.00, user_id=1, description='Философский роман')
                ]
                db.session.add_all(books)
                db.session.commit()
                print("✅ Тестовые книги добавлены")
        
        return jsonify({
            'message': 'База данных инициализирована успешно',
            'details': {
                'users_count': User.query.count(),
                'books_count': Book.query.count(),
                'database': 'PostgreSQL',
                'connection': 'postgres@www:5432/bookshelf_db'
            }
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API ЭНДПОИНТЫ ==========

@app.route('/')
def home():
    return jsonify({
        'name': 'Bookshelf API',
        'version': '2.0',
        'database': 'PostgreSQL',
        'endpoints': {
            'GET /api/books': 'Получить все книги',
            'POST /api/books': 'Создать книгу',
            'POST /api/users': 'Создать пользователя',
            'GET /api/init-db': 'Инициализировать базу данных'
        }
    })

@app.route('/api/books', methods=['GET'])
def get_books():
    """Получить все книги"""
    try:
        books = Book.query.all()
        result = []
        for book in books:
            book_data = {
                'id': book.id,
                'title': book.title,
                'author': book.author or 'Неизвестен',
                'year': book.year,
                'price': book.price,
                'quantity': book.quantity,
                'description': book.description or ''
            }
            result.append(book_data)
        
        return jsonify({
            'count': len(result),
            'books': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books', methods=['POST'])
def create_book():
    """Создать новую книгу"""
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
        
        return jsonify({
            'message': 'Книга успешно создана',
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Создать нового пользователя"""
    try:
        data = request.get_json()
        
        if not data.get('username'):
            return jsonify({'error': 'Имя пользователя обязательно'}), 400
        if not data.get('email'):
            return jsonify({'error': 'Email обязателен'}), 400
        if not data.get('password'):
            return jsonify({'error': 'Пароль обязателен'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Пользователь успешно создан',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== ПРОСТЫЕ ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ ==========

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Тест подключения к базе данных"""
    try:
        users_count = User.query.count()
        books_count = Book.query.count()
        
        return jsonify({
            'status': 'success',
            'message': 'Подключение к базе данных работает',
            'stats': {
                'users': users_count,
                'books': books_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка подключения к базе: {str(e)}'
        }), 500

@app.route('/api/reset-db', methods=['GET'])
def reset_database():
    """Сброс базы данных (только для тестирования!)"""
    try:
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            admin = User(username='admin', email='admin@example.com', password='admin123')
            db.session.add(admin)
            db.session.commit()
            
            books = [
                Book(title='Война и мир', author='Лев Толстой', year=1869, price=500.00, user_id=1),
                Book(title='1984', author='Джордж Оруэлл', year=1949, price=300.50, user_id=1),
                Book(title='Мастер и Маргарита', author='Михаил Булгаков', year=1967, price=450.00, user_id=1)
            ]
            db.session.add_all(books)
            db.session.commit()
        
        return jsonify({'message': 'База данных сброшена и переинициализирована'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == '__main__':
    print("=" * 60)
    print("📚 BOOKSHELF API WITH POSTGRESQL")
    print("=" * 60)
    print("Подключение к: postgres:1234@www:5432/bookshelf_db")
    print("=" * 60)
    print("Доступные команды:")
    print("1. http://localhost:5000/              - Информация об API")
    print("2. http://localhost:5000/api/init-db   - Инициализация БД")
    print("3. http://localhost:5000/api/books     - Все книги")
    print("4. http://localhost:5000/api/test-connection - Тест подключения")
    print("=" * 60)
    
    try:
        with app.app_context():
            db.engine.connect()
            print("✅ Подключение к базе данных успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе: {e}")
        print("Проверьте:")
        print("1. Запущен ли PostgreSQL на сервере 'www'")
        print("2. Правильный ли пароль в строке подключения")
        print("3. Существует ли база 'bookshelf_db'")
        print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')

# Мельников Андрей 03.02 15:51

