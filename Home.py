from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'azerguest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

# ========================================
# DATABASE MODELS
# ========================================

class Place(db.Model):
    """Məkan modeli"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # dag, deniz, tarix, macera, gol
    region = db.Column(db.String(120), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    views = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert place to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'region': self.region,
            'price': self.price,
            'rating': self.rating,
            'views': self.views,
            'image': self.image,
            'description': self.description
        }


class Favorite(db.Model):
    """Sevimli məkanlar modeli"""
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    user_id = db.Column(db.Integer, default=1)  # Demo üçün default user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    place = db.relationship('Place', backref='favorites')


class Testimonial(db.Model):
    """Rəy modeli"""
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    text = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    """Rezervasiya modeli"""
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    user_name = db.Column(db.String(120), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    place = db.relationship('Place', backref='bookings')


# ========================================
# DATABASE INITIALIZATION
# ========================================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()
        
        if Place.query.count() == 0:
            sample_places = [
                Place(name='Göygöl', category='gol', region='Gəncə-Qazax', price=50, rating=4.8, views=2567, 
                      image='./assets/img/114f9a2ec33af4cc6204a9ec1ef7893a.jpg', 
                      description='Gözəl təbiət və təmiz hava'),
                      
                Place(name='Böyük Qafqaz dağları', category='dag', region='Şimal', price=85, rating=4.9, views=1234,
                      image='./assets/img/b1ed4c30ca688758ad1df626823f3e9d.jpg',
                      description='Dağ turizmi və hiking'),
                      
                Place(name='Şəki Xan sarayı', category='tarix', region='Şəki-Zaqatala', price=40, rating=4.7, views=856,
                      image='./assets/img/d80231b02fc0ee33596e4b3ad7093174.jpg',
                      description='Tarixi abidə və memarlıq'),
                      
                Place(name='Nohur gölü', category='gol', region='Qəbələ', price=110, rating=4.9, views=3421,
                      image='./assets/img/f407fe6a8ada9d1e8234c27432a0d291.jpg',
                      description='Sakit göl və piknik'),
                      
                Place(name='Şahdağ', category='dag', region='Qusar', price=95, rating=4.8, views=2890,
                      image='./assets/img/44b52ba9e8ae6016db193e363f587dc1.jpg',
                      description='Qış turizmi və xizək'),
                      
                Place(name='Lahıc', category='macera', region='İsmayıllı', price=85, rating=4.6, views=1567,
                      image='./assets/img/bd6b575e4a642c8623419a2e042634d1.jpg',
                      description='Dağ kəndi və sənətkarlıq'),
                      
                Place(name='İçərişəhər', category='tarix', region='Bakı', price=70, rating=4.9, views=4123,
                      image='./assets/img/d81dd0d67b5c1ddfbbb7518278daeaf3.jpg',
                      description='Qədim şəhər və muzeylər'),
                      
                Place(name='Xəzər dənizi sahili', category='deniz', region='Abşeron', price=60, rating=4.5, views=3456,
                      image='./assets/img/114f9a2ec33af4cc6204a9ec1ef7893a.jpg',
                      description='Çimərlik və su əyləncələri'),
                      
                Place(name='Quba dağları', category='dag', region='Quba', price=75, rating=4.7, views=2134,
                      image='./assets/img/b1ed4c30ca688758ad1df626823f3e9d.jpg',
                      description='Təbiət və trekking'),
                      
                Place(name='Lənkəran sahili', category='deniz', region='Lənkəran', price=45, rating=4.6, views=1890,
                      image='./assets/img/d80231b02fc0ee33596e4b3ad7093174.jpg',
                      description='Subtropik iqlim və çay'),
                      
                Place(name='Qobustan', category='tarix', region='Abşeron', price=55, rating=4.8, views=2678,
                      image='./assets/img/f407fe6a8ada9d1e8234c27432a0d291.jpg',
                      description='Qədim qaya rəsmləri'),
                      
                Place(name='Tufandağ', category='macera', region='Qəbələ', price=120, rating=4.9, views=3890,
                      image='./assets/img/44b52ba9e8ae6016db193e363f587dc1.jpg',
                      description='Dağ kurort və aktivlər')
            ]
            
            db.session.bulk_save_objects(sample_places)
            
            sample_testimonials = [
                Testimonial(author='Aytən Məmmədova', role='Müştəri', 
                          text='Platforma çox yaxşıdır, səyahətimi asanlaşdırdı.', 
                          avatar='https://i.pravatar.cc/60?img=1', rating=5.0),
                Testimonial(author='Elçin Həsənov', role='Müştəri',
                          text='Səyahətlərim daha rahat və əlçatan oldu.',
                          avatar='https://i.pravatar.cc/60?img=2', rating=4.8),
                Testimonial(author='Leyla Qasımova', role='Müştəri',
                          text='AzerGuest ilə Azərbaycanda gəzmək çox asandır.',
                          avatar='https://i.pravatar.cc/60?img=3', rating=4.9)
            ]
            
            db.session.bulk_save_objects(sample_testimonials)
            db.session.commit()
            print("Database initialized with sample data!")


# ========================================
# ROUTES
# ========================================

@app.route('/')
def index():
    """Ana səhifə"""
    places = Place.query.order_by(Place.rating.desc()).limit(12).all()
    testimonials = Testimonial.query.all()
    return render_template('home.html', places=places, testimonials=testimonials)


@app.route('/place/<int:place_id>')
def place_detail(place_id):
    """Məkan detallı səhifə"""
    place = Place.query.get_or_404(place_id)
    place.views += 1
    db.session.commit()
    return render_template('place.html', place=place)


# ========================================
# API ENDPOINTS
# ========================================

@app.route('/api/places', methods=['GET'])
def api_get_places():
    """Bütün məkanları gətir"""
    places = Place.query.all()
    return jsonify([place.to_dict() for place in places])


@app.route('/api/places/filter', methods=['POST'])
def api_filter_places():
    """Məkanları filtr et"""
    data = request.get_json()
    
    query = Place.query
    
    # Category filter
    categories = data.get('categories', [])
    if categories:
        query = query.filter(Place.category.in_(categories))
    
    # Price range filter
    price_min = data.get('priceMin', 0)
    price_max = data.get('priceMax', 1000)
    query = query.filter(Place.price >= price_min, Place.price <= price_max)
    
    # Rating filter
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


@app.route('/api/search', methods=['GET'])
def api_search():
    """Axtarış"""
    q_from = request.args.get('from')
    q_to = request.args.get('to')
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = Place.query
    
    if q_from:
        query = query.filter(Place.region.ilike(f"%{q_from}%"))
    if q_to:
        query = query.filter(Place.region.ilike(f"%{q_to}%"))
    
    places = query.all()
    
    return jsonify({
        'success': True,
        'count': len(places),
        'places': [place.to_dict() for place in places]
    })


@app.route('/api/favorites', methods=['GET'])
def api_get_favorites():
    """Sevimli məkanları gətir"""
    favorites = Favorite.query.filter_by(user_id=1).all()
    place_ids = [fav.place_id for fav in favorites]
    places = Place.query.filter(Place.id.in_(place_ids)).all()
    
    return jsonify({
        'success': True,
        'count': len(places),
        'places': [place.to_dict() for place in places]
    })


@app.route('/api/favorites/add', methods=['POST'])
def api_add_favorite():
    """Sevimli məkana əlavə et"""
    data = request.get_json()
    place_id = data.get('place_id')
    
    if not place_id:
        return jsonify({'success': False, 'message': 'place_id tələb olunur'}), 400
    
    # Check if already exists
    existing = Favorite.query.filter_by(place_id=place_id, user_id=1).first()
    if existing:
        return jsonify({'success': False, 'message': 'Artıq sevimlilərdə var'})
    
    favorite = Favorite(place_id=place_id, user_id=1)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Sevimli məkana əlavə edildi'})


@app.route('/api/favorites/remove', methods=['POST'])
def api_remove_favorite():
    """Sevimli məkandan sil"""
    data = request.get_json()
    place_id = data.get('place_id')
    
    if not place_id:
        return jsonify({'success': False, 'message': 'place_id tələb olunur'}), 400
    
    favorite = Favorite.query.filter_by(place_id=place_id, user_id=1).first()
    if not favorite:
        return jsonify({'success': False, 'message': 'Sevimlilərdə tapılmadı'})
    
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Sevimlilərdən silindi'})


@app.route('/api/booking', methods=['POST'])
def api_create_booking():
    """Rezervasiya yarat"""
    data = request.get_json()
    
    required_fields = ['place_id', 'user_name', 'user_email', 'start_date', 'end_date', 'guests']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'{field} tələb olunur'}), 400
    
    place = Place.query.get(data['place_id'])
    if not place:
        return jsonify({'success': False, 'message': 'Məkan tapılmadı'}), 404
    
    # Calculate total price
    from datetime import datetime as dt
    start = dt.strptime(data['start_date'], '%Y-%m-%d').date()
    end = dt.strptime(data['end_date'], '%Y-%m-%d').date()
    days = (end - start).days
    total_price = place.price * data['guests'] * days
    
    booking = Booking(
        place_id=data['place_id'],
        user_name=data['user_name'],
        user_email=data['user_email'],
        start_date=start,
        end_date=end,
        guests=data['guests'],
        total_price=total_price
    )
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Rezervasiya yaradıldı',
        'booking_id': booking.id,
        'total_price': total_price
    })


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
    app.run(debug=True, host='0.0.0.0', port=5000)