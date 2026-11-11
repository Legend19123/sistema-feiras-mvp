from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-mvp-segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feiras.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Utilizador(db.Model):
    __tablename__ = 'utilizadores'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Feirante(db.Model):
    __tablename__ = 'feirantes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    setor_barraca = db.Column(db.String(50), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    taxas = db.relationship('Taxa', backref='feirante', lazy=True, cascade='all, delete-orphan')

class Taxa(db.Model):
    __tablename__ = 'taxas'
    id = db.Column(db.Integer, primary_key=True)
    semana_referencia = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    valor = db.Column(db.Float, nullable=False, default=50.0)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    feirante_id = db.Column(db.Integer, db.ForeignKey('feirantes.id'), nullable=False)

@app.route('/')
def index():
    if 'utilizador_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        utilizador = Utilizador.query.filter_by(username=username).first()
        if utilizador and bcrypt.check_password_hash(utilizador.password_hash, password):
            session['utilizador_id'] = utilizador.id
            session['username'] = utilizador.username
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'utilizador_id' not in session:
        return redirect(url_for('login'))
    feirantes = Feirante.query.all()
    return render_template('dashboard.html', feirantes=feirantes)

@app.route('/feirante/novo', methods=['GET', 'POST'])
def novo_feirante():
    if 'utilizador_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome = request.form['nome']
        documento = request.form['documento']
        setor = request.form['setor_barraca']
        telefone = request.form['telefone']
        
        existente = Feirante.query.filter_by(documento=documento).first()
        if existente:
            flash('Já existe um feirante cadastrado com este documento.', 'danger')
            return redirect(url_for('novo_feirante'))
            
        novo = Feirante(nome=nome, documento=documento, setor_barraca=setor, telefone=telefone)
        db.session.add(novo)
        db.session.commit()
        
        taxa_inicial = Taxa(valor=50.0, status='pendente', feirante_id=novo.id)
        db.session.add(taxa_inicial)
        db.session.commit()
        
        flash('Feirante cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('cadastro.html')

@app.route('/taxa/alternar/<int:taxa_id>')
def alternar_taxa(taxa_id):
    if 'utilizador_id' not in session:
        return redirect(url_for('login'))
    taxa = Taxa.query.get_or_404(taxa_id)
    taxa.status = 'pago' if taxa.status == 'pendente' else 'pendente'
    db.session.commit()
    flash('Estado da taxa atualizado com sucesso!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Utilizador.query.filter_by(username='gestora.feira').first():
            hashed_pw = bcrypt.generate_password_hash('senha123').decode('utf-8')
            admin = Utilizador(username='gestora.feira', password_hash=hashed_pw)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)




