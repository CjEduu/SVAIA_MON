
import ansi2html
import requests
import toml
from flask import Flask, app, flash, redirect, render_template, request, url_for

app = Flask(__name__, template_folder="templates")
app.config.from_file("config.toml",load=toml.load)
app.secret_key = app.config['SECRET_KEY']
API = app.config['API_ENDPOINT']

from flask import make_response

# WARNING: I SHOULD HAVE A SECOND LOOK ON EVERYTHING BECAUSE I CHANGED THINGS TO DEVELOP

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        api_endpoint = f"{API}/login"
        credentials = {
            'nombre': request.form['username'],
            'password': request.form['password']
        }
        print("Cookies enviadas al backend:", request.cookies)
        response = requests.post(
            api_endpoint,
            json=credentials,
            cookies=request.cookies
        )
        print("Respuesta del backend:", response.status_code, response.text)
        print("Cookies en la respuesta:", response.cookies.get_dict())
        if response.status_code == 200:
            flask_response = make_response(redirect('/'))
            if 'access_token' in response.cookies:
                flask_response.set_cookie(
                    'access_token',
                    response.cookies['access_token'],
                    httponly=True,
                    secure=False,
                    samesite='Strict'
                )
            flash('Login exitoso', 'success')
            return flask_response
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    resp = requests.post(f"{API}/is_logged",cookies=request.cookies)
    if resp.status_code == 200:
        flask_response = make_response(redirect(url_for('login')))
        flask_response.set_cookie('access_token', '', expires=0, httponly=True, secure=False, samesite='Strict', path='/')
        flask_response.set_cookie('remember_token', '', expires=0, httponly=True, secure=False, samesite='Strict', path='/')
        flash('Sesión cerrada exitosamente', 'success')
        return flask_response
    else:
        flash('Tienes que iniciar sesión primero')
        return redirect(url_for('login'))

@app.route("/chat")
def chat():
    response = requests.get(f"{API}/proyectos", cookies=request.cookies)
    if response.status_code == 200:
        proyectos = response.json()
        return render_template("chat.html", proyectos=proyectos)
    else:
        proyectos = []
        flash('Error al obtener la lista de proyectos para el chat. Por favor, inicia sesión.', 'danger')
        return redirect(url_for("index"))
    

#template correcto
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/usuarios")
def usuarios():
    response = requests.get(f"{API}/usuarios", cookies=request.cookies)
    if response.status_code == 200:
        usuarios = response.json()
    else:
        usuarios = []
        flash('Error al obtener la lista de usuarios. Por favor, inicia sesión.', 'danger')
    print(type(usuarios), usuarios)
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/usuarios/crear",methods = ["GET"])
def crear_usuario():
    resp = requests.post(f"{API}/is_logged",cookies=request.cookies)
    if resp.status_code==200:
        return render_template("crear_usuario.html")
    else:
        flash("Es necesario iniciar sesión")
        return redirect(url_for("index"))


#template correcto
@app.route("/usuarios/editar/<string:nombre_usuario>", methods=["POST", "GET"])
def editar_usuario(nombre_usuario):
    resp = requests.get(f"{API}/usuario/{nombre_usuario.strip()}")
    if resp.status_code != 200:
        return redirect(url_for("index"))
    usuario = resp.json()
    return render_template("editar_usuario.html",usuario=usuario)


#template correcto
@app.route("/proyectos")
def proyectos():
    #Lo suyo sería comprobar si est́a loggeado con un post a la API
    response = requests.get(f"{API}/proyectos", cookies=request.cookies)
    if response.status_code == 200:
        proyectos = response.json()
    else:
        proyectos = []
        flash('Error al obtener la lista de proyectos.', 'danger')
    print(type(proyectos), proyectos)
    return render_template("proyectos.html", proyectos=proyectos)

#template correcto
@app.route("/proyectos/eliminar", methods=["POST"])
def eliminar_proyecto():
    next = request.form.get("next", url_for("proyectos"))
    return redirect(next, url_for("proyectos"))

#template correcto
@app.route("/proyectos/editar/<string:nombre_proyecto>", methods=["GET"])
def editar_proyecto(nombre_proyecto):
    proyecto = requests.get(f"{API}/proyecto/{nombre_proyecto}").json()
    if proyecto.get("error",None) is not None:
       return redirect(url_for("index"))

    print(proyecto.get("sec_info"))
    return render_template("editar_proyecto.html", proyecto=proyecto,sec_info=proyecto.get("sec_info"))

@app.route("/i_personal")
def i_personal():
    response = requests.get(f"{API}/i_personal", cookies=request.cookies)
    if response.status_code == 200:
        usuario = response.json()
        return render_template("i_personal.html", usuario=usuario)
    flash('Error al obtener la información personal. Por favor, inicia sesión.', 'danger')
    return redirect(url_for("index"))


@app.route("/proyectos/crear")
def crear_proyecto():
    response = requests.post(f"{API}/is_logged", cookies=request.cookies)
    if response.status_code != 200:
        flash('Error al mostrar formulario. Por favor, inicia sesión.', 'danger')
        return redirect(url_for("index"))
    return render_template("crear_proyecto.html")
        

@app.route("/proyectos/<string:nombre_proyecto>")
def ver_proyecto(nombre_proyecto):
    """
        Implementar alguna manera de introducir el token en la parte del front para cuando se introduzca empezar a monitorizar.
    """
    response = requests.get(f"{API}/proyecto/{nombre_proyecto}",cookies=request.cookies)
    if response.status_code != 200:
        flash('Error buscando el proyecto')
        return redirect(url_for("proyectos"))

    proyecto=response.json()
    print(proyecto)
    return render_template("metricas_proyecto.html",project=proyecto,sec_info=proyecto.get('sec_info',None),analysis_result=proyecto.get('analysis_result',None),cves=proyecto.get('related_cves',None))

@app.route("/cve/<string:cve_id>")
def ver_cve(cve_id):
    response = requests.get(f"{API}/cve/{cve_id}",cookies=request.cookies)
    if response.status_code != 200:
        flash('Error buscando el cve')
        return redirect(url_for("index"))

    cve=response.json()
    converter = ansi2html.Ansi2HTMLConverter(inline=True)
    cve["literal_formatted"] = converter.convert(cve["literal_formatted"],full=False)
    return render_template("cve.html", cve=cve)


