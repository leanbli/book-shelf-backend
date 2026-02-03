"""
Bookshelf API - Backend для CRUD приложения "Книжная полка"
REST API на Flask для управления книгами
"""

#leanbli - Сидорова Варвара 03.02.26

from flask import Flask, request, jsonify
from flask_cors import CORS

# ========== СОЗДАНИЕ ПРИЛОЖЕНИЯ ==========
app = Flask(__name__)
CORS(app)  # Разрешаем запросы с фронтенда

# ========== "БАЗА ДАННЫХ" (в памяти) ==========
books = [
    {"id": 1, "title": "Война и мир", "author": "Лев Толстой", "year": 1869},
    {"id": 2, "title": "1984", "author": "Джордж Оруэлл", "year": 1949},
    {"id": 3, "title": "Мастер и Маргарита", "author": "Михаил Булгаков", "year": 1967},
    {"id": 4, "title": "Преступление и наказание", "author": "Фёдор Достоевский", "year": 1866},
    {"id": 5, "title": "Гарри Поттер и философский камень", "author": "Джоан Роулинг", "year": 1997},
]

next_id = 6  # Следующий свободный ID

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def find_book_by_id(book_id):
    """Найти книгу по ID"""
    for book in books:
        if book['id'] == book_id:
            return book
    return None

def validate_book_data(data, for_update=False):
    """Валидация данных книги"""
    errors = []
    
    # Проверка для создания новой книги
    if not for_update:
        if 'title' not in data or not data['title'].strip():
            errors.append("Поле 'title' обязательно")
    
    # Проверка года
    if 'year' in data and data['year'] is not None:
        try:
            year = int(data['year'])
            if year < 1000 or year > 2026:
                errors.append("Год должен быть между 1000 и 2026")
        except (ValueError, TypeError):
            errors.append("Год должен быть числом")
    
    return errors

# ========== REST API ЭНДПОИНТЫ ==========

@app.route('/')
def home():
    """Главная страница API"""
    return jsonify({
        "name": "Bookshelf API",
        "version": "1.0.0",
        "description": "REST API для управления книгами",
        "endpoints": {
            "GET /api/books": "Получить все книги",
            "GET /api/books/<id>": "Получить книгу по ID",
            "POST /api/books": "Добавить новую книгу",
            "PUT /api/books/<id>": "Обновить книгу",
            "DELETE /api/books/<id>": "Удалить книгу"
        }
    })

@app.route('/api/books', methods=['GET'])
def get_books():
    """Получить все книги"""
    return jsonify(books)

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Получить книгу по ID"""
    book = find_book_by_id(book_id)
    if book is None:
        return jsonify({"error": "Книга не найдена"}), 404
    return jsonify(book)

@app.route('/api/books', methods=['POST'])
def create_book():
    """Создать новую книгу"""
    global next_id
    
    # Получаем данные из запроса
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "Неверный формат JSON"}), 400
    
    # Валидация
    errors = validate_book_data(data, for_update=False)
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Создание новой книги
    new_book = {
        "id": next_id,
        "title": data.get('title', '').strip(),
        "author": data.get('author', '').strip() or None,
        "year": data.get('year')
    }
    
    # Преобразуем год в число, если он есть
    if new_book['year'] is not None:
        new_book['year'] = int(new_book['year'])
    
    # Добавляем в "базу данных"
    books.append(new_book)
    next_id += 1
    
    return jsonify(new_book), 201  # 201 Created

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Обновить существующую книгу"""
    book = find_book_by_id(book_id)
    if book is None:
        return jsonify({"error": "Книга не найдена"}), 404
    
    # Получаем данные из запроса
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "Неверный формат JSON"}), 400
    
    # Валидация
    errors = validate_book_data(data, for_update=True)
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Обновляем только переданные поля
    if 'title' in data:
        book['title'] = data['title'].strip()
    if 'author' in data:
        book['author'] = data['author'].strip() or None
    if 'year' in data:
        book['year'] = int(data['year']) if data['year'] is not None else None
    
    return jsonify(book)

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Удалить книгу"""
    global books
    
    initial_length = len(books)
    books = [b for b in books if b['id'] != book_id]
    
    if len(books) == initial_length:
        return jsonify({"error": "Книга не найдена"}), 404
    
    return jsonify({"message": "Книга удалена"})

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == '__main__':
    print("=" * 50)
    print("📚 Bookshelf API Server")
    print("=" * 50)
    print("Сервер запущен: http://127.0.0.1:5000")
    print("API доступен по: http://127.0.0.1:5000/api/books")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 50)
    app.run(debug=True, port=5000)
