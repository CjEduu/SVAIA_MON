import datetime
import uuid
from os import path

import requests
import toml
from flask import Flask, app, jsonify, make_response, request
from flask_cors import CORS
from flask_praetorian import (
    Praetorian,
    auth_required,
    current_user,
)
from sqlalchemy import (
    String,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
)
from web_api.models import (
    CVE,
    AnalysisResult,
    Base,
    Proyectos,
    Roles,
    SecInfo,
    user_roles,
)

app = Flask(__name__, template_folder="templates")
app.config.from_file("config.toml",load=toml.load)
app.secret_key = app.config['SECRET_KEY']
app.config['PRAETORIAN_HASH_SCHEME'] = 'argon2'
SBOM_API_ENDPOINT:str = str(app.config['SBOM_API_ENDPOINT'])

guard = Praetorian()
cors = CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})


if app.debug:
    basedir = path.abspath(path.dirname(__file__))
    engine = create_engine(
    f"sqlite:///{path.join(basedir, '..', 'mock-bd', 'svaia_db.db')}",
    echo=True
    )
else:
    engine =create_engine(
        app.config['DB_URI'],
        echo=True
    )


class Users(Base):
    __tablename__ = "UsersNew"
    id: Mapped[str] = mapped_column(String(36))
    nombre: Mapped[str] = mapped_column(String(30),primary_key = True)
    apellidos: Mapped[str] = mapped_column(String(60))
    correo: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column("password",String(120))

    roles:Mapped[list[Roles]] = relationship("Roles", secondary=user_roles,back_populates="users")

    is_active = True
    def is_valid(self):
        return self.is_active

    @property
    def identity(self):
        return self.nombre

    @property
    def password(self):
        return self.hashed_password

    @property
    def rolenames(self):
        roles = [rol.rol for rol in self.roles]
        return roles

    @classmethod
    def identify(cls,nombre):
        with Session(engine) as session:
            user = session.query(cls).options(joinedload(cls.roles)).get(nombre)
        return user

    @classmethod
    def lookup(cls,nombre):
        with Session(engine) as session:
            user = session.query(cls).options(joinedload(cls.roles)).filter_by(nombre=nombre).one_or_none()
        return user

    def to_dict(self) -> dict:
        return {'id' : self.id,
                'nombre':self.nombre,
                'apellidos':self.apellidos,
                'correo':self.correo,
                'hashed_password':self.hashed_password,
                'roles':[role.rol for role in self.roles]
                }

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.nombre!r}, rol={self.roles!r},passwordHash={self.password!r})"

guard.init_app(app,Users)
cors.init_app(app)
       
@app.route("/api/is_logged",methods=['POST'])
#@auth_required
def is_logged():
    return jsonify({"ok":True}),200
    
@app.route("/api/login", methods=['POST'])
def login():
    print("Cookies recibidas:", request.cookies)
    data = request.json
    username = data.get('nombre')
    password = data.get('password')
    print(f"Intento de login: {username}")
    try:
        user = guard.authenticate(username, password)
    except Exception as e:
        print(f"Error en autenticación: {e}")
        return jsonify({"error": "Username and/or password are incorrect"}), 400
    access_token = guard.encode_jwt_token(user)
    response = make_response(jsonify({"ok": True}), 200)
    response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Strict')
    print("Cookie enviada:", response.headers.get('Set-Cookie'))
    return response

@app.route("/api/usuario/<string:nombre_usuario>",methods=['GET'])
def get_usuario(nombre_usuario):
    with Session(engine) as session:
        query = select(Users).where(Users.nombre == nombre_usuario.strip())
        usuario = session.execute(query).scalars().first()
        if usuario is None:
            return jsonify({"error":f"Usuario {nombre_usuario} no encontrado"}),400
        usuario = usuario.to_dict()

    return jsonify(usuario),200


#template correcto
@app.route("/api/usuarios",methods=['GET'])
#@auth_required
def get_usuarios():
    with Session(engine) as session:
        query = select(Users)
        usuarios = session.execute(query).scalars().all()
        usuarios = [ usuario.to_dict() for usuario in usuarios]

    return jsonify(usuarios),200


#template correcto
@app.route("/api/usuarios/crear",methods=["POST"])
#@auth_required
def crear_usuario():
    data = request.json
    nombre = data.get('nombre').lower().strip()
    apellidos = data.get('apellidos',None)
    password = data.get('password')
    password = guard.hash_password(password)
    correo = data.get('correo')
    roles = data.get('roles',[])
    roles.append('Base')
    roles = set(roles)
    id = str(uuid.uuid4())
    nuevo_usuario = Users(id=id,nombre=nombre,apellidos=apellidos,hashed_password=password,correo=correo)
   
    with Session(engine) as session:
        roles_existentes = session.query(Roles).where(Roles.rol.in_(roles)).all()
        missing_roles = {rol.lower().strip() for rol in roles} - { rol.rol for rol in roles_existentes}
        if missing_roles:
            return jsonify({"error":f"Roles no encontrados: {missing_roles}"}),400
            
        query = select(Users).where(Users.nombre == nombre)
        result = session.execute(query).first()
        if result is not None:
            return jsonify({"error":"El usuario ya existe"}),400

        nuevo_usuario.roles = roles_existentes
        user_dict = nuevo_usuario.to_dict() #Estrictamente necesario hacerlo aquí por la forma en que SQLALchemy carga los objetos
        session.add(nuevo_usuario)
        session.commit()
        
    return jsonify(user_dict),200

#template correcto
@app.delete("/api/usuarios/eliminar/<string:nombre>")
def eliminar_usuario(nombre:str):
    nombre = nombre.strip() # Necesario sanitizar para evitar sqlinjection? : NO, lo hace SQLAlchemy
    with Session(engine) as session:
        query = select(Users).where(Users.nombre == nombre)
        usuario = session.scalars(query).first()
        if usuario is None:
            return jsonify({"error":"El usuario no existe"}),400

        session.delete(usuario)
        session.commit()
    return jsonify({"ok":True}),200


#template correcto
@app.patch("/api/usuarios/editar/<string:nombre>")
def editar_usuario(nombre:str):
    data = request.json
    nombre = nombre.strip() 

    with Session(engine) as session:
        query = select(Users).where(Users.nombre == nombre)
        usuario = session.scalars(query).first()
        if usuario is None:
            return jsonify({"error":"El usuario no existe"}),400

        usuario.apellidos = data.get("apellidos", usuario.apellidos)
        usuario.correo = data.get('correo',usuario.correo)
        usuario.roles = data.get('rol',usuario.roles)
        nueva_password = data.get('password',None)
        if nueva_password:
            usuario.hashed_password = guard.hash_password(nueva_password)  # <- usa tu función de hash

        session.commit()
        return jsonify(usuario.to_dict()),200

@app.route("/api/proyecto/<string:nombre_proyecto>",methods=['GET'])
def get_proyecto(nombre_proyecto):
    with Session(engine) as session:
        query = select(Proyectos).where(nombre_proyecto == Proyectos.nombre)
        proyecto_ = session.scalars(query).first()
        if proyecto_ is None:
            return jsonify({"error":f"El proyecto {nombre_proyecto} no existe"}),400

        proyecto_ = proyecto_.to_dict()    
        return jsonify(proyecto_),200

#template correcto
@app.route("/api/proyectos",methods=['GET'])
#@auth_required
def get_proyectos():
    with Session(engine) as session:
        query = select(Proyectos)
        proyectos_ = session.scalars(query).all()
        proyectos_ = [ p.to_dict() for p in proyectos_]
    return jsonify(proyectos_),200

#template correcto
@app.route("/api/proyectos/crear",methods = ["POST"])
def crear_proyecto():
    # Datos básicos 
    data = request.json
    nombre = data.get("nombre","Proyecto Nuevo").strip()
    descripcion = data.get("descripcion","")
    owner=data.get("owner","Proyecto Nuevo")
    nivelCVSS = data.get("nivelCVSS")
    nivelIntegridad = data.get("nivelIntegridad")   
    nivelConfidencialidad = data.get("nivelConfidencialidad")    
    nivelDisponibilidad = data.get("nivelDisponibilidad")
    sbom = data.get("sbom")

    fecha_creacion = datetime.datetime.now()
    fecha_edicion = datetime.datetime.now()
        

    # Solícitamos el análisis del SBOM
    sbom_analysis_response = requests.post(
        SBOM_API_ENDPOINT,
        json = sbom
    )

    if not sbom_analysis_response.ok:
        return jsonify(sbom_analysis_response.json()),400
    
    analysis_data = sbom_analysis_response.json()
    print(analysis_data)

    # Proyecto tal cual
    nuevo_proyecto = Proyectos(
        nombre=nombre,owner=owner,descripcion=descripcion,
        fecha_creacion=fecha_creacion,fecha_edicion=fecha_edicion)

    # SecInfo related (Thresholds etc)
    nueva_sec_info = SecInfo(
        nombre_proyecto=nombre,nivelCVSS=nivelCVSS,nivelIntegridad=nivelIntegridad,
        nivelConfidencialidad=nivelConfidencialidad,nivelDisponibilidad=nivelDisponibilidad,
        sbomHash=hash(str(sbom))        
    )

    # Resultado de los análisis de nuestro proyecto
    nuevo_analisis_result = AnalysisResult(
        actualNivelCVSS= analysis_data["actualNivelCVSS"],
        actualNivelIntegridad= analysis_data["actualNivelIntegridad"],
        actualNivelConfidencialidad= analysis_data["actualNivelConfidencialidad"],
        actualNivelDisponibilidad= analysis_data["actualNivelDisponibilidad"]
    )

    # CVES encontrados
    cve_objects = [
        CVE(
            nombre_proyecto=nombre,
            cve_id=cve_data.get('id').strip(),
            cvss=cve_data.get('cvss'),
            confidencialidad=cve_data.get('confidencialidad'),
            integridad=cve_data.get('integridad'),
            disponibilidad=cve_data.get('disponibilidad'),
            literal_formatted=cve_data.get('literal_formatted'),
            url=cve_data.get('url')
        )
        for cve_data in analysis_data["CVES"]
    ]    

    # Assemble!
    with Session(engine) as session:
        nuevo_proyecto.sec_info = nueva_sec_info
        nuevo_proyecto.analysis_result = nuevo_analisis_result
        nuevo_proyecto.related_cves = cve_objects
        session.add(nuevo_proyecto)
        session.commit()

    return jsonify({"ok":True}),200

#template correcto
@app.delete("/api/proyectos/eliminar/<string:nombre>")
def eliminar_proyecto(nombre):
    nombre = nombre.strip()
    with Session(engine) as session:
        query = select(Proyectos).where(Proyectos.nombre == nombre)
        proyecto = session.scalars(query).first()
        print(proyecto)
        if proyecto is None:
            return jsonify({"error":f"El proyecto {nombre} no existe" }),400
        
        session.delete(proyecto)
        session.commit()

    return jsonify({"ok":True}),200


# TODO ANALIZAR SI SE INCLUYE UN NUEVO SBOM
@app.patch("/api/proyectos/editar/<string:nombre>")
def editar_proyecto(nombre):
        with Session(engine) as session:
            query = select(Proyectos).where(Proyectos.nombre == nombre)
            proyecto = session.scalar(query)
            if proyecto is None:
                return jsonify({"error":f"El proyecto {nombre} no existe" }),400

            # He cambiado la opcion de hacer que se diga si realmente no han habido cambios por ser poco legible/eficiente... si realmente fuera necesario incluirla
            # simplemente para cambiar el proyecto creariamos un objeto proyecto desde 0 y lo comparariamos con el ya existente, habria que añadir método __eq__ a la clase Proyectos.
            data = request.json
            proyecto.nombre = data.get('nombre',proyecto.nombre)
            proyecto.owner = data.get('owner',proyecto.owner)
            proyecto.descripcion = data.get('descripcion',proyecto.descripcion)

            proyecto.sec_info.nivelCVSS = data.get("nivelCVSS",proyecto.sec_info.nivelCVSS)
            proyecto.sec_info.nivelIntegridad = data.get("nivelIntegridad",proyecto.sec_info.nivelIntegridad)   
            proyecto.sec_info.nivelConfidencialidad = data.get("nivelConfidencialidad",proyecto.sec_info.nivelConfidencialidad)    
            proyecto.sec_info.nivelDisponibilidad = data.get("nivelDisponibilidad",proyecto.sec_info.nivelDisponibilidad)            

            proyecto.fecha_edicion = datetime.datetime.now()

            session.commit()

        return jsonify({"ok":True}),200


@app.route("/api/cve/<string:cve_id>")
@auth_required
def get_cve(cve_id):
    with Session(engine) as session:
        query = select(CVE).where(CVE.cve_id == cve_id)
        cve_ = session.scalars(query).first()
        if cve_ is None:
            return jsonify({"error":f"El cve {cve_id} no está registrado"}),400

        cve_ = cve_.to_dict()    
        return jsonify(cve_),200


@app.route("/api/i_personal")
@auth_required
def i_personal():
    user = current_user()
    return jsonify(user.to_dict()),200


@app.route("/api/test/<string:password>")
def test(password):
    return guard.hash_password(password)
