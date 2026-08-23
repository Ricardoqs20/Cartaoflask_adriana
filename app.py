import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

template_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(template_dir, 'templates'), static_folder=os.path.join(template_dir, 'static'))
app.secret_key = 'chave_secreta_super_segura'

UPLOAD_FOLDER = os.path.join(template_dir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///imoveis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Imovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    preco_num = db.Column(db.Float, nullable=False)
    preco = db.Column(db.String(50), nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(250), nullable=False)
    link = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    imoveis = Imovel.query.order_by(Imovel.preco_num.desc()).all()
    perfil = {"nome": "Adriana Lobão", "corretora": "RE/MAX DREAMS", "subtitulo": "O seu estilo de vida merece um imóvel à altura.", "foto": "corretora.png"}
    return render_template("index.html", perfil=perfil, imoveis=imoveis)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == "adminadmin":
            session['admin_logado'] = True
            return redirect(url_for("admin_painel"))
        else:
            erro = "Senha incorreta!"
    return render_template("login.html", erro=erro)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logado', None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
def admin_painel():
    if not session.get('admin_logado'):
        return redirect(url_for("admin_login"))
    
    imoveis = Imovel.query.order_by(Imovel.id.desc()).all()
    
    # Impede que o navegador guarde cache da página protegida, forçando o pedido de senha
    response = make_response(render_template("admin.html", imoveis=imoveis))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/admin/adicionar", methods=["GET", "POST"])
def adicionar_imovel():
    if not session.get('admin_logado'): return redirect(url_for("admin_login"))
    
    if request.method == "POST":
        titulo = request.form.get("titulo")
        preco_limpo = request.form.get("preco_num").replace(".", "").replace(",", "")
        preco_num = float(preco_limpo) if preco_limpo else 0.0
        preco_formatado = f"R$ {int(preco_num):,}".replace(",", ".")
        localizacao = request.form.get("localizacao")
        link = request.form.get("link")

        file = request.files.get('imagem_arquivo')
        if file and file.filename != '':
            extensao = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            filename = f"{uuid.uuid4()}.{extensao}"
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagem_path = f"uploads/{filename}"
        else:
            imagem_path = "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=800&auto=format&fit=crop"

        novo = Imovel(titulo=titulo, preco_num=preco_num, preco=preco_formatado, localizacao=localizacao, imagem=imagem_path, link=link)
        db.session.add(novo)
        db.session.commit()
        return redirect(url_for("admin_painel"))

    return render_template("adicionar.html")

@app.route("/admin/editar/<int:id>", methods=["GET", "POST"])
def editar_imovel(id):
    if not session.get('admin_logado'): return redirect(url_for("admin_login"))
    imovel = Imovel.query.get_or_404(id)

    if request.method == "POST":
        imovel.titulo = request.form.get("titulo")
        preco_limpo = request.form.get("preco_num").replace(".", "").replace(",", "")
        imovel.preco_num = float(preco_limpo) if preco_limpo else 0.0
        imovel.preco = f"R$ {int(imovel.preco_num):,}".replace(",", ".")
        imovel.localizacao = request.form.get("localizacao")
        imovel.link = request.form.get("link")

        file = request.files.get('imagem_arquivo')
        if file and file.filename != '':
            extensao = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            filename = f"{uuid.uuid4()}.{extensao}"
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imovel.imagem = f"uploads/{filename}"

        db.session.commit()
        return redirect(url_for("admin_painel"))

    return render_template("editar.html", imovel=imovel)

@app.route("/admin/excluir/<int:id>")
def excluir_imovel(id):
    if not session.get('admin_logado'): return redirect(url_for("admin_login"))
    imovel = Imovel.query.get_or_404(id)
    if imovel.imagem.startswith('uploads/'):
        path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(imovel.imagem))
        if os.path.exists(path): os.remove(path)
    db.session.delete(imovel)
    db.session.commit()
    return redirect(url_for("admin_painel"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)