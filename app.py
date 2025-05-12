from flask import Flask, render_template, request, redirect, send_file, url_for, session, flash
from database import get_db_connection, init_db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete'

# Initialiser la base de données
init_db()

# Page d'accueil

VALID_PASSWORD = "021984"  # Le mot de passe attendu (code)

@app.route('/', methods=['GET', 'POST'])
def connexion():
    if session.get('user_logged_in'):  # Vérifiez si l'utilisateur est déjà connecté
        return redirect(url_for('index'))  # Rediriger vers la page d'accueil si l'utilisateur est connecté

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vérification du mot de passe
        if password == VALID_PASSWORD:
            session['user_logged_in'] = True  # Marquer l'utilisateur comme connecté
            return redirect(url_for('index'))  # Rediriger vers la page d'accueil après la connexion
        else:
            # Affichage d'une erreur si le mot de passe est incorrect
            flash(" mot de passe incorrect.", "danger")
            return render_template('connexion.html', error="Mot de passe incorrect!")

    return render_template('connexion.html')

@app.route('/index')
def index():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    return render_template('index.html')

@app.route('/deconnexion')
def deconnexion():
    session.pop('user_logged_in', None)
    return redirect(url_for('connexion'))

# Liste des clients
@app.route('/clients')
def clients():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    return render_template('clients.html', clients=clients)

# Ajouter un client
@app.route('/clients/ajouter', methods=('GET', 'POST'))
def add_client():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['telephone']
        email = request.form['email']

        conn = get_db_connection()
        conn.execute('INSERT INTO clients (nom, telephone, email) VALUES (?, ?, ?)', (nom, telephone, email))
        conn.commit()
        conn.close()
        return redirect(url_for('clients'))
    return render_template('add_client.html')

# Liste des produits
@app.route('/produits')
def produits():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    produits = conn.execute('SELECT * FROM produits').fetchall()
    conn.close()
    return render_template('produits.html', produits=produits)

# Ajouter un produit
@app.route('/produits/ajouter', methods=('GET', 'POST'))
def add_produit():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    if request.method == 'POST':
        nom = request.form['nom']
        conn = get_db_connection()
        conn.execute('INSERT INTO produits (nom) VALUES (?)', (nom,))
        conn.commit()
        conn.close()
        return redirect(url_for('produits'))
    return render_template('add_produit.html')

@app.route("/ajouter_categorie", methods=["GET", "POST"])
def ajouter_categorie():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    if request.method == "POST":
        nom = request.form["nom"]
        conn = get_db_connection()
        conn.execute("INSERT INTO categories (nom) VALUES (?)", (nom,))
        conn.commit()
        conn.close()
        return redirect("/ajouter_categorie")
    return render_template("ajouter_categorie.html")

@app.route("/categories")
def categories():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("categories.html", categories=categories)


@app.route('/client/<int:client_id>')
def client_detail(client_id):
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupération du client
    client = cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
    
    # Si le client n'existe pas, rediriger
    if not client:
        return redirect(url_for('index'))

    conn.close()
    return render_template('client_detail.html', client=client)

# Ajouter un reçu
@app.route('/ajouter_recu', methods=['GET', 'POST'])
def ajouter_recu():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    client_id = request.args.get('client_id')
    clients = cursor.execute("SELECT * FROM clients").fetchall()
    produits = cursor.execute("SELECT * FROM produits").fetchall()
    categories = cursor.execute("SELECT * FROM categories").fetchall()


    if request.method == 'POST':
        client_id = request.form.get('client_id')
        nom_temporaire = request.form.get('nom_temporaire')
        statut = int(request.form.get('statut'))

        produits_ids = request.form.getlist('produit_id')
        quantites = request.form.getlist('quantite')
        categories_ids = request.form.getlist('categorie_id')
        prix_unitaires = request.form.getlist('prix')

        total = 0
        for i in range(len(produits_ids)):
            q = int(quantites[i])
            p = float(prix_unitaires[i])
            total += q * p

        cursor.execute('''
            INSERT INTO recu (client_id, nom_client_temporaire, total, solde)
            VALUES (?, ?, ?, ?)
        ''', (client_id if client_id else None, nom_temporaire, total, statut))
        recu_id = cursor.lastrowid

        for i in range(len(produits_ids)):
            cursor.execute('''
                INSERT INTO recu_produits (recu_id, produit_id, quantite, prix_unitaire, categorie_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (recu_id, produits_ids[i], quantites[i], prix_unitaires[i], categories_ids[i]))

        conn.commit()
        conn.close()
        return redirect(url_for('tous_les_recus'))

    conn.close()
    return render_template('ajouter_recu.html', clients=clients, produits=produits, categories=categories, selected_client_id=client_id)

# Reçus d'un client
@app.route('/client/<int:client_id>/recus')
def recus_client(client_id):
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    cursor = conn.cursor()

    client = cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    recus = cursor.execute("SELECT * FROM recu WHERE client_id = ? ORDER BY date DESC", (client_id,)).fetchall()

    recus_details = []
    for recu in recus:
        produits = cursor.execute('''
            SELECT p.nom, rp.quantite, rp.prix_unitaire, c.nom as categorie_nom
            FROM recu_produits rp
            JOIN produits p ON p.id = rp.produit_id
            JOIN categories c ON c.id = rp.categorie_id
            WHERE rp.recu_id = ?
        ''', (recu[0],)).fetchall()
        recus_details.append((recu, produits))

    conn.close()
    return render_template("tous_recus.html", client=client, recus_details=recus_details)


# Liste de tous les reçus
# Liste de tous les reçus
@app.route('/recus')
def tous_les_recus():
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    client_id = request.args.get('client_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Si un client_id est passé, on filtre par ce client, sinon on récupère tous les reçus
    if client_id:
        cursor.execute("""
            SELECT r.*, c.nom AS nom_client
            FROM recu r
            LEFT JOIN clients c ON r.client_id = c.id
            WHERE r.client_id = ?
            ORDER BY r.id DESC
        """, (client_id,))
    else:
        cursor.execute("""
            SELECT r.*, c.nom AS nom_client
            FROM recu r
            LEFT JOIN clients c ON r.client_id = c.id
            ORDER BY r.id DESC
        """)

    # Récupération de tous les reçus
    recus = cursor.fetchall()

    recus_details = []
    for recu in recus:
        # Récupérer les produits associés à chaque reçu
        produits = conn.execute("""
            SELECT p.nom, rp.quantite, rp.prix_unitaire, c.nom AS categorie_nom
            FROM recu_produits rp
            JOIN produits p ON rp.produit_id = p.id
            JOIN categories c ON c.id = rp.categorie_id
            WHERE rp.recu_id = ?
        """, (recu[0],)).fetchall()  # Utilisation de l'index pour accéder à 'id' du reçu

        # Ajout de l'information du reçu et des produits à la liste
        recus_details.append((recu, produits))

    conn.close()
    
    # Passage des détails des reçus et de l'id du client sélectionné au template
    return render_template('tous_recus.html', recus_details=recus_details, selected_client_id=client_id)

# Bascule du statut de solde
@app.route('/recu/<int:recu_id>/basculer_solde')
def basculer_solde(recu_id):
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    cursor = conn.cursor()

    recu = cursor.execute("SELECT solde FROM recu WHERE id = ?", (recu_id,)).fetchone()
    if recu:
        nouveau_statut = 0 if recu[0] == 1 else 1
        cursor.execute("UPDATE recu SET solde = ? WHERE id = ?", (nouveau_statut, recu_id))
        conn.commit()

    conn.close()
    return redirect(request.referrer or url_for('index'))


@app.route('/recu/<int:recu_id>/imprimer')
def imprimer_recu(recu_id):
    if not session.get('user_logged_in'):
        return redirect(url_for('connexion'))
    conn = get_db_connection()
    cursor = conn.cursor()

    recu = cursor.execute("SELECT * FROM recu WHERE id = ?", (recu_id,)).fetchone()
    client = cursor.execute("SELECT * FROM clients WHERE id = ?", (recu["client_id"],)).fetchone() if recu["client_id"] else None

    produits = cursor.execute('''
        SELECT p.nom, rp.quantite, rp.prix_unitaire, c.nom AS categorie_nom
        FROM recu_produits rp
        JOIN produits p ON p.id = rp.produit_id
        JOIN categories c ON c.id = rp.categorie_id
        WHERE rp.recu_id = ?
    ''', (recu_id,)).fetchall()

    conn.close()

    # Taille de l'image plus grande
    width, height = 1000, max(1200, 400 + len(produits) * 50)
    bg_color = (250, 250, 255)
    accent_color = (0, 123, 255)
    text_color = (0, 0, 0)
    gray = (100, 100, 100)
    green = (34, 139, 34)
    red = (220, 20, 60)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 34)
        font_subtitle = ImageFont.truetype("arialbd.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 22)
    except:
        font_title = font_subtitle = font_text = ImageFont.load_default()

    # Titre
    y = 40
    draw.text((width // 2 - 100, y), f"REÇU N°{recu['id']}", font=font_title, fill=accent_color)
    y += 60

    # Infos client
    x_pad = 50
    draw.rectangle([x_pad - 20, y - 10, width - x_pad + 20, y + 250], outline=accent_color, width=4)

    draw.text((x_pad, y), f"ID Client : {recu['client_id']}", font=font_text, fill=text_color)
    y += 35
    draw.text((x_pad, y), f"Nom du client : {client['nom'] if client else recu['nom_client_temporaire']}", font=font_text, fill=text_color)
    y += 35
    draw.text((x_pad, y), f"Solde : {'Soldé' if recu['solde'] else 'Non soldé'}", font=font_text, fill=green if recu['solde'] else red)
    y += 35
    draw.text((x_pad, y), f"Date : {recu['date']}", font=font_text, fill=gray)
    y += 35
    draw.text((x_pad, y), f"Total : {recu['total']} FCFA", font=font_text, fill=accent_color)
    y += 60

    # Produits associés
    draw.text((x_pad, y), "Produits associés :", font=font_subtitle, fill=accent_color)
    y += 40

    for i, produit in enumerate(produits):
        bg = (255, 255, 255) if i % 2 == 0 else (240, 248, 255)
        draw.rectangle([x_pad - 10, y - 5, width - x_pad + 10, y + 40], fill=bg)
        text = f"{produit['nom']} (x{produit['quantite']}) | {produit['prix_unitaire']} FCFA | {produit['categorie_nom']}"
        draw.text((x_pad, y), text, font=font_text, fill=text_color)
        y += 50

    # Bas
    y += 30
    draw.line([x_pad - 10, y, width - x_pad + 10, y], fill=accent_color, width=2)
    y += 15
    draw.text((x_pad, y), "Merci de votre confiance !", font=font_text, fill=(80, 80, 80))

    # Sauvegarde en image PNG
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=f"recu_{recu_id}.png")

# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True)
