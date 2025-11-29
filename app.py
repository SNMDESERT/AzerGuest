from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'azerguest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db = SQLAlchemy(app)


# ========================================
# DATABASE MODELS
# ========================================

class User(db.Model):
    """İstifadəçi modeli"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tourist data fields
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    family = db.Column(db.Integer, default=0)
    region = db.Column(db.String(120), nullable=True)
    trips_per_year = db.Column(db.Integer, default=0)
    avg_budget_per_year = db.Column(db.Integer, default=0)
    favorite_destination = db.Column(db.String(120), nullable=True)
    vacation_type = db.Column(db.String(120), nullable=True)
    travel_interest = db.Column(db.Integer, default=5)
    
    # Profile
    avatar = db.Column(db.String(255), default='https://i.pravatar.cc/200')
    bio = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.String(50), default='Yeni Səyyah')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'gender': self.gender,
            'age': self.age,
            'family': self.family,
            'region': self.region,
            'trips_per_year': self.trips_per_year,
            'avg_budget_per_year': self.avg_budget_per_year,
            'favorite_destination': self.favorite_destination,
            'vacation_type': self.vacation_type,
            'travel_interest': self.travel_interest,
            'avatar': self.avatar,
            'bio': self.bio,
            'points': self.points,
            'level': self.level,
            'member_since': self.created_at.strftime('%Y-%m-%d')
        }


class Place(db.Model):
    """Məkan modeli"""
    __tablename__ = 'places'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(120), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    views = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'region': self.region,
            'price': self.price,
            'rating': self.rating,
            'views': self.views,
            'image': self.image,
            'description': self.description,
            'features': self.features
        }


class Booking(db.Model):
    """Rezervasiya modeli"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='bookings')
    place = db.relationship('Place', backref='bookings')


class Review(db.Model):
    """Rəy modeli"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reviews')
    place = db.relationship('Place', backref='reviews')


class Favorite(db.Model):
    """Sevimli məkanlar modeli"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='favorites')
    place = db.relationship('Place', backref='favorites')


# ========================================
# HELPER FUNCTIONS
# ========================================

def calculate_user_level(points):
    """İstifadəçi səviyyəsini hesabla"""
    if points < 100:
        return 'Yeni Səyyah'
    elif points < 500:
        return 'Aktiv Səyyah'
    elif points < 1000:
        return 'Təcrübəli Səyyah'
    elif points < 2000:
        return 'Ekspert Səyyah'
    else:
        return 'Ulduz Səyyah'


# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Qeydiyyat"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'email', 'password', 'gender', 'age', 'region']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'success': False, 'message': f'{field} tələb olunur'}), 400
            
            # Check if user exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'message': 'Bu email artıq qeydiyyatdan keçib'}), 400
            
            # Create user
            hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
            
            new_user = User(
                name=data['name'],
                email=data['email'],
                password=hashed_password,
                phone=data.get('phone', ''),
                gender=data['gender'],
                age=int(data['age']),
                family=int(data.get('family', 0)),
                region=data['region'],
                trips_per_year=int(data.get('trips_per_year', 0)),
                avg_budget_per_year=int(data.get('avg_budget_per_year', 0)),
                favorite_destination=data.get('favorite_destination', ''),
                vacation_type=data.get('vacation_type', ''),
                travel_interest=int(data.get('travel_interest', 5)),
                points=50,
                level='Yeni Səyyah'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # Login user
            session['user_id'] = new_user.id
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Qeydiyyat uğurlu oldu!',
                'user': new_user.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            return jsonify({'success': False, 'message': f'Xəta: {str(e)}'}), 500
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'success': False, 'message': 'Email və şifrə tələb olunur'}), 400
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                return jsonify({'success': False, 'message': 'Email və ya şifrə yanlışdır'}), 401
            
            session['user_id'] = user.id
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Giriş uğurlu oldu!',
                'user': user.to_dict()
            })
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'success': False, 'message': f'Xəta: {str(e)}'}), 500
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Çıxış"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    """Profil səhifəsi"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=user)


# ========================================
# MAIN ROUTES
# ========================================

@app.route('/')
def index():
    """Ana səhifə"""
    places = Place.query.order_by(Place.rating.desc()).limit(12).all()
    
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    
    return render_template('home.html', places=places, user=user)


# ========================================
# API ENDPOINTS
# ========================================

@app.route('/api/places', methods=['GET'])
def api_get_places():
    """Bütün məkanları gətir"""
    try:
        places = Place.query.all()
        return jsonify([place.to_dict() for place in places])
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/places/filter', methods=['POST'])
def api_filter_places():
    """Məkanları filtr et"""
    try:
        data = request.get_json()
        
        query = Place.query
        
        categories = data.get('categories', [])
        if categories:
            query = query.filter(Place.category.in_(categories))
        
        price_min = data.get('priceMin', 0)
        price_max = data.get('priceMax', 1000)
        query = query.filter(Place.price >= price_min, Place.price <= price_max)
        
        ratings = data.get('ratings', [])
        if ratings:
            min_rating = min(ratings)
            query = query.filter(Place.rating >= min_rating)
        
        places = query.all()
        return jsonify({
            'success': True,
            'count': len(places),
            'places': [place.to_dict() for place in places]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/favorites', methods=['GET'])
def api_get_favorites():
    """Sevimli məkanları gətir"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Giriş tələb olunur'}), 401
    
    try:
        favorites = Favorite.query.filter_by(user_id=session['user_id']).all()
        place_ids = [fav.place_id for fav in favorites]
        places = Place.query.filter(Place.id.in_(place_ids)).all()
        
        return jsonify({
            'success': True,
            'count': len(places),
            'places': [place.to_dict() for place in places]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/favorites/add', methods=['POST'])
def api_add_favorite():
    """Sevimli məkana əlavə et"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Giriş tələb olunur'}), 401
    
    try:
        data = request.get_json()
        place_id = data.get('place_id')
        
        if not place_id:
            return jsonify({'success': False, 'message': 'place_id tələb olunur'}), 400
        
        existing = Favorite.query.filter_by(place_id=place_id, user_id=session['user_id']).first()
        if existing:
            return jsonify({'success': False, 'message': 'Artıq sevimlilərdə var'})
        
        favorite = Favorite(place_id=place_id, user_id=session['user_id'])
        db.session.add(favorite)
        
        # Award points
        user = User.query.get(session['user_id'])
        user.points += 5
        user.level = calculate_user_level(user.points)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Sevimli məkana əlavə edildi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/favorites/remove', methods=['POST'])
def api_remove_favorite():
    """Sevimli məkandan sil"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Giriş tələb olunur'}), 401
    
    try:
        data = request.get_json()
        place_id = data.get('place_id')
        
        favorite = Favorite.query.filter_by(place_id=place_id, user_id=session['user_id']).first()
        if not favorite:
            return jsonify({'success': False, 'message': 'Sevimlilərdə tapılmadı'})
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Sevimlilərdən silindi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/user/current', methods=['GET'])
def api_current_user():
    """Cari istifadəçi"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Giriş tələb olunur'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'İstifadəçi tapılmadı'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========================================
# DATABASE INITIALIZATION
# ========================================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        print("✅ Database cədvəlləri yaradıldı!")
        
        # Add sample places if empty
        if Place.query.count() == 0:
            sample_places = [
                Place(name='Göygöl', category='gol', region='Gəncə-Qazax', price=50, rating=4.8, views=2567, 
                      image='./assets/img/114f9a2ec33af4cc6204a9ec1ef7893a.jpg', 
                      description='Gözəl təbiət və təmiz hava', features='WiFi, Restoran, Parking'),
                      
                Place(name='Böyük Qafqaz dağları', category='dag', region='Şimal', price=85, rating=4.9, views=1234,
                      image='./assets/img/b1ed4c30ca688758ad1df626823f3e9d.jpg',
                      description='Dağ turizmi və hiking', features='Treking, Kamp, Bələdçi'),
                      
                Place(name='Şəki Xan sarayı', category='tarix', region='Şəki-Zaqatala', price=40, rating=4.7, views=856,
                      image='./assets/img/d80231b02fc0ee33596e4b3ad7093174.jpg',
                      description='Tarixi abidə və memarlıq', features='Muzey, Ekskursiya, Foto'),
                      
                Place(name='Nohur gölü', category='gol', region='Qəbələ', price=110, rating=4.9, views=3421,
                      image='./assets/img/f407fe6a8ada9d1e8234c27432a0d291.jpg',
                      description='Sakit göl və piknik', features='Qayıq, Balıq ovu, Piknik'),
                      
                Place(name='Şahdağ', category='dag', region='Qusar', price=95, rating=4.8, views=2890,
                      image='./assets/img/44b52ba9e8ae6016db193e363f587dc1.jpg',
                      description='Qış turizmi və xizək', features='Xizək, Teleferik, Otel'),
                      
                Place(name='Lahıc', category='macera', region='İsmayıllı', price=85, rating=4.6, views=1567,
                      image='./assets/img/bd6b575e4a642c8623419a2e042634d1.jpg',
                      description='Dağ kəndi və sənətkarlıq', features='Sənətkarlıq, Tarixi evlər'),
                      
                Place(name='İçərişəhər', category='tarix', region='Bakı', price=70, rating=4.9, views=4123,
                      image='./assets/img/d81dd0d67b5c1ddfbbb7518278daeaf3.jpg',
                      description='Qədim şəhər və muzeylər', features='Muzeylər, Mağazalar, Restoranlar'),
                      
                Place(name='Xəzər dənizi sahili', category='deniz', region='Abşeron', price=60, rating=4.5, views=3456,
                      image='./assets/img/114f9a2ec33af4cc6204a9ec1ef7893a.jpg',
                      description='Çimərlik və su əyləncələri', features='Çimərlik, Su idmanı, Kafe'),
                      
                Place(name='Quba dağları', category='dag', region='Quba', price=75, rating=4.7, views=2134,
                      image='./assets/img/b1ed4c30ca688758ad1df626823f3e9d.jpg',
                      description='Təbiət və trekking', features='Kamp, Treking, Təbiət'),
                      
                Place(name='Lənkəran sahili', category='deniz', region='Lənkəran', price=45, rating=4.6, views=1890,
                      image='./assets/img/d80231b02fc0ee33596e4b3ad7093174.jpg',
                      description='Subtropik iqlim və çay', features='Çimərlik, Çay bağları'),
                      
                Place(name='Qobustan', category='tarix', region='Abşeron', price=55, rating=4.8, views=2678,
                      image='./assets/img/f407fe6a8ada9d1e8234c27432a0d291.jpg',
                      description='Qədim qaya rəsmləri', features='Muzey, Palçıq vulkanı'),
                      
                Place(name='Tufandağ', category='macera', region='Qəbələ', price=120, rating=4.9, views=3890,
                      image='./assets/img/44b52ba9e8ae6016db193e363f587dc1.jpg',
                      description='Dağ kurort və aktivlər', features='Xizək, Teleferik, Restoran')
            ]
            
            db.session.bulk_save_objects(sample_places)
            db.session.commit()
            print("✅ Sample məkanlar əlavə edildi!")


# ========================================
# ERROR HANDLERS
# ========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Tapılmadı'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Server xətası'}), 500


# ========================================
# RUN APPLICATION
# ========================================

if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("🚀 AzerGuest Server işə başladı!")
    print("📍 URL: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)