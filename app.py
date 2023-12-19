from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
import os
import base64
from pymongo import MongoClient
from flask import session
from bson import ObjectId
from bson import ObjectId
from datetime import datetime
import secrets
from werkzeug.exceptions import NotFound
from flask import abort

app = Flask(__name__)
app.secret_key = os.urandom(24)


client = MongoClient('mongodb+srv://alifwrdhh111:sparta@cluster0.b0osqyt.mongodb.net/eCommerceDB?retryWrites=true&w=majority')
eCommerceDB = client['eCommerceDB']


products_collection = eCommerceDB['products']
collection = eCommerceDB['hmm']
question_collection = eCommerceDB['question']
app.secret_key = secrets.token_hex(16)


#halaman utama pada saat running
@app.route('/')
def redirect_to_home():
    return redirect(url_for('user_home'))

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(24).hex()  
    return session['_csrf_token']

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        
        product_data = {
            'name': request.form['name'],
            'image': request.form['image'],
            'description': request.form['description'],
            'price': float(request.form['price']),

            
        }
        products_collection.insert_one(product_data)
        return redirect(url_for('admin'))

    elif request.method == 'GET':
        products = products_collection.find()
        return render_template('admin/admin.html', products=products)

@app.route('/user/signin')
def user_signin():
    csrf_token = generate_csrf_token()  
    return render_template('user/signin.html', csrf_token=csrf_token)

@app.route('/signin', methods=['POST'])
def sign_in():
    if request.method == 'POST':
        
        if request.form['_csrf_token'] != session.pop('_csrf_token', None):
            abort(403)  
        
        
        
        email = request.form['email']
        password = request.form['password']
        
        
        
        user = collection.find_one({'email': email, 'password': password})
        if user:
            
            return "Sign in successful"
        else:
            
            return "Invalid credentials"

    return "Invalid request"

@app.route('/admin/delete/<product_id>')
def delete_product(product_id):
    products_collection.delete_one({'_id': ObjectId(product_id)})
    return redirect(url_for('admin'))


@app.route('/admin/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = products_collection.find_one({'_id': ObjectId(product_id)})

    if product is None:
        raise NotFound(f"Product with ID {product_id} not found")

    if request.method == 'POST':
        
        updated_data = {
            'name': request.form['name'],
            'image': request.form['image'],
            'description': request.form.get('description', ''),
            'price': float(request.form['price']),
            
        }
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': updated_data})
        return redirect(url_for('admin'))

    return render_template('admin/edit_product.html', product=product)



@app.route('/user/home')
def user_home():
    return render_template('user/home.html')
@app.route('/products')
def user_products():
    products = products_collection.find()  
    return render_template('user/products.html', products=products)


@app.route('/product/<product_id>')
def product_detail(product_id):
    product = products_collection.find_one({'_id': ObjectId(product_id)})  
    return render_template('user/detail_product.html', product=product)

from flask import abort
@app.route('/user/detail_product/<product_id>', methods=['GET', 'POST'])
def detail_product(product_id):
    try:
        product_id_obj = ObjectId(product_id)
    except Exception as e:
        print(f"Invalid ObjectId: {e}")
        return redirect(url_for('user_products'))

    
    product = products_collection.find_one({'_id': product_id_obj})

    if not product:
        
        abort(404)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])

        if 'cart' not in session:
            session['cart'] = []

        existing_item = next((item for item in session['cart'] if item['product_id'] == str(product['_id'])), None)

        if existing_item:
            
            existing_item['quantity'] += quantity
            existing_item['total_price'] = existing_item['quantity'] * product['price']
        else:
            
            session['cart'].append({
                'product_id': str(product['_id']),
                'product_name': product['name'],
                'description': product['deskription'],
                'image': product['image'],
                'quantity': quantity,
                'price': product['price'],
                'total_price': quantity * product['price'],
                'total_orders': 1
            })

        return redirect(url_for('user_products'))

    return render_template('user/detail_product.html', product=product)


@app.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        
        product_id_obj = ObjectId(product_id)
    except Exception as e:
        
        print(f"Invalid ObjectId: {e}")
        return redirect(url_for('user_products'))

    
    product = products_collection.find_one({'_id': product_id_obj})

    if not product:
        
        return render_template('404.html'), 404

    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        existing_item = next((item for item in session['cart'] if item['product_id'] == str(product['_id'])), None)

        if existing_item:
            
            existing_item['quantity'] += quantity
            existing_item['total_price'] = existing_item['quantity'] * product['price']
            
            existing_item['description'] = product.get('deskription', 'Deskripsi tidak tersedia')
        else:
            
            session['cart'].append({
                'product_id': str(product['_id']),
                'product_name': product['name'],
                'quantity': quantity,
                'description': product.get('deskription', 'Deskripsi tidak tersedia'), 
                'total_price': quantity * product['price']
            })

        return redirect(url_for('checkout'))
    
    return render_template('user/products.html', products=products_collection.find())



@app.route('/user/checkout', methods=['GET', 'POST'])
def checkout():
    
    cart = session.get('cart', [])

    if request.method == 'POST':
        
        
        for item in cart:
            product_id = ObjectId(item['product_id'])
            product_name = item['product_name']
            quantity = item['quantity']
            total_price = item['total_price']
            description = item.get('description', 'Deskripsi tidak tersedia')

            
            

        
        session.pop('cart', None)

        
        return redirect(url_for('checkout_success'))

    
    total_price = sum(item['total_price'] for item in cart)

    return render_template('user/checkout.html', cart=cart, total_price=total_price)


@app.route('/user/checkout_success')
def checkout_success():
    return render_template('user/checkout_success.html')


@app.route('/user/about')
def user_about():
    return render_template('user/about.html')


@app.route('/user/pertanyaan', methods=['GET'])
def user_pertanyaan():
    
    questions = list(question_collection.find())
    questions_with_username = []

    for question in questions:
        
        user_id = question.get('user_id')
        user_details = collection.find_one({'_id': ObjectId(user_id)})

        
        if user_details:
            question_with_username = {
                'date': question.get('date'),
                'question': question.get('question'),
                'answer_status': question.get('answer_status'),
                'username': f"{user_details.get('first_name', '')} {user_details.get('last_name', '')}"
            }
            questions_with_username.append(question_with_username)

    return render_template('user/pertanyaan.html', questions=questions_with_username)

@app.route('/user/pertanyaan', methods=['POST'])
def submit_pertanyaan():
    
    question = request.form.get('question')
    current_date = datetime.now().strftime('%Y-%m-%d')  
    
    
    user_id = '65812677b5c5ed6f364170f6'  
    
    
    question_collection.insert_one({
        'user_id': ObjectId(user_id),
        'date': current_date,  
        'question': question,
        'answer_status': 'Not answered'
    })

    
    return redirect(url_for('user_pertanyaan'))

@app.route('/admin/bukakk')
def index():
    
    questions = list(question_collection.find().sort('date', -1))  

    
    for question in questions:
        user_id = question.get('user_id')
        if user_id:
            user_data = collection.find_one({'_id': user_id})
            if user_data:
                question['username'] = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"

    return render_template('admin/bukakk.html', questions=questions)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if request.method == 'POST':
        try:
            answer_text = request.form['answerText']
            question_id = request.form['questionId']

            if answer_text and question_id:
                question_collection.update_one({'_id': ObjectId(question_id)}, {'$set': {'answer_status': answer_text}})
                return jsonify({'status': 'success', 'message': 'Answer updated successfully'})
            else:
                return jsonify({'status': 'error', 'message': 'Invalid data received'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'Method not allowed'})



@app.route('/user/kontak')
def user_kontak():
    return render_template('user/kontak.html')

@app.route('/user/signup')
def signup():
    return render_template('user/signup.html')

@app.route('/signup', methods=['POST'])
def sign_up():
    if request.method == 'POST':
        first_name = request.form['nama_depan']
        last_name = request.form['nama_belakang']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['konfirmasi-password']
        role = request.form['role']

        role = request.form['role']

        user_profile = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'role': role
        }

        result = collection.insert_one(user_profile)

        if result.inserted_id:
            if role == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user_home'))
        else:
            return "Failed to insert data"

    return "Invalid request"

@app.route('/user/editprofil')
def edit_profile():
    
    user_id = ObjectId('65812677b5c5ed6f364170f6')

    
    user_data = collection.find_one({"_id": user_id})

    if user_data:
        
        return render_template('user/editprofil.html', user=user_data)
    else:
        return "User not found"  

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if request.method == 'POST':
        user_id = ObjectId(request.form['user_id'])
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        
        user_data = collection.find_one({"_id": user_id})

        if user_data:
            
            if old_password == user_data['password']:
                
                updated_data = {
                    "first_name": request.form['nama-depan'],
                    "last_name": request.form['nama-belakang'],
                    "email": request.form['email']
                }
                
                
                if new_password:
                    updated_data["password"] = new_password
                
                
                if 'foto' in request.files:
                    foto = request.files['foto']
                    if foto.filename != '':
                        encoded_image = base64.b64encode(foto.read()).decode('utf-8')
                        updated_data["profile_picture"] = encoded_image
                
                collection.update_one({"_id": user_id}, {"$set": updated_data})
                return redirect(url_for('edit_profile'))
            else:
                return "Incorrect old password"
        else:
            return "User not found"  

    return "Method not allowed"

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
