from flask import Flask, render_template,request,redirect,url_for,session
from flask import flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask import g
import forms
from models import db
from models import Cliente, IngredientePizza, DetallePizza
from models import Usuario
from forms import RegistroForm
from ModelUser import ModelUser
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required
from datetime import datetime
from sqlalchemy import cast, Date
from datetime import datetime, date


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf=CSRFProtect()

login_manager_app=LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db,id)

@app.errorhandler(400)
def page_not_found(e):
	return render_template('404.html'),404

#@app.route("/")
#@app.route("/index")
#def index():
#	create_form=forms.UserForm2(request.form)
#	alumno=Alumnos.query.all() #Esto significa que estamos haciendo: select * from alumnos
#	return render_template("index.html", form=create_form,alumnos=alumno)


@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/inicio_sesion", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        
        usuario_loggeado = ModelUser.login(db, username)
        
        if usuario_loggeado is not None:
            
            if check_password_hash(usuario_loggeado.password, password):
                session['user_id'] = usuario_loggeado.id
                login_user(usuario_loggeado)
                return redirect(url_for('index'))
            else:
                flash("La contraseña no es correcta")
        else:
            flash("Usuario no encontrado")

    return render_template('/inicio_sesion.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))




@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()
    
    if form.validate_on_submit():

        nuevo_usuario = Usuario(
            username=form.username.data,
            password=form.password.data,
            fullname=form.fullname.data
        )
        

        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))  
    
    return render_template('registro.html', form=form)




@app.route('/buscar_ventas_por_fecha', methods=['POST'])
def buscar_ventas_por_fecha():
    try:
        
        fecha_str = request.form.get('fecha_busqueda')
        fecha_busqueda = datetime.strptime(fecha_str, '%m/%d/%Y').date()
        
        
        ventas = db.session.query(Cliente).filter(
            cast(Cliente.created_date, Date) == fecha_busqueda
        ).all()
        
        
        total_ventas = sum(venta.total for venta in ventas) if ventas else 0
        
        
        return render_template('index.html', 
                            ventas_hoy=ventas, 
                            total_ventas_hoy=total_ventas,
                            tabla=True,
                            fecha_busqueda=fecha_busqueda.strftime('%d/%m/%Y'))
    
    except ValueError:
        flash('Formato de fecha inválido. Use el formato MM/DD/YYYY', 'error')
        return redirect(url_for('index'))


@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@login_required
def index():
    formularioP = forms.FormPizza(request.form)
    formularioC = forms.UserForm(request.form)
    fecha_busqueda = None

    # Manejar búsqueda por fecha
    if request.method == 'POST' and 'fecha_busqueda' in request.form:
        try:
            fecha_str = request.form.get('fecha_busqueda')
            fecha_busqueda = datetime.strptime(fecha_str, '%m/%d/%Y').date()
            
            ventas_hoy = db.session.query(Cliente).filter(
                cast(Cliente.created_date, Date) == fecha_busqueda
            ).all()
            
            total_ventas_hoy = sum(venta.total for venta in ventas_hoy) if ventas_hoy else 0
            
            if 'cliente_data' in session:
                formularioC.nombre.data = session['cliente_data'].get('nombre', '')
                formularioC.direccion.data = session['cliente_data'].get('direccion', '')
                formularioC.telefono.data = session['cliente_data'].get('telefono', '')

            tabla = colocarTabla()
            
            return render_template('index.html',
                                formularioP=formularioP,
                                formularioC=formularioC,
                                tabla=tabla,
                                ventas_hoy=ventas_hoy,
                                total_ventas_hoy=total_ventas_hoy,
                                fecha_busqueda=fecha_busqueda.strftime('%d/%m/%Y'))
        
        except ValueError:
            flash('Formato de fecha inválido. Use el formato MM/DD/YYYY', 'error')

    
    if 'cliente_data' in session:
        formularioC.nombre.data = session['cliente_data'].get('nombre', '')
        formularioC.direccion.data = session['cliente_data'].get('direccion', '')
        formularioC.telefono.data = session['cliente_data'].get('telefono', '')

    if request.method == 'POST' and formularioP.validate_on_submit():
        session['cliente_data'] = {
            'nombre': formularioC.nombre.data,
            'direccion': formularioC.direccion.data,
            'telefono': formularioC.telefono.data
        }

        if not formularioP.ingredientes.data:
            flash('Debes seleccionar al menos un ingrediente', 'danger')
            return redirect(url_for('index'))

        agregarPizza(formularioP.tamanio.data, formularioP.numerop.data,
                     formularioP.ingredientes.data)
        flash('Se ha agregado una pizza a la tabla', 'success')
        return redirect(url_for('index'))

    tabla = colocarTabla()

    # Obtener ventas del día actual
    hoy = date.today()
    ventas_hoy = db.session.query(Cliente).filter(
        cast(Cliente.created_date, Date) == hoy
    ).all()
    total_ventas_hoy = sum(venta.total for venta in ventas_hoy) if ventas_hoy else 0

    return render_template('index.html',
                         formularioP=formularioP,
                         formularioC=formularioC,
                         tabla=tabla,
                         ventas_hoy=ventas_hoy,
                         total_ventas_hoy=total_ventas_hoy)

def agregarPizza(tamanio, numerop, ingredientes):
    ingredientes_lista = ",".join(ingredientes)
    with open("tablaPizza.txt", "a", encoding="utf-8") as archivo:
        archivo.write(f"{tamanio}|{numerop}|{ingredientes_lista}\n")

def colocarTabla():
    carrito = []
    try:
        with open("tablaPizza.txt", "r", encoding="utf-8") as archivo:
            for linea in archivo:
                datos = linea.strip().split("|")
                if len(datos) >= 3:
                    carrito.append({
                        "tamanio": datos[0],
                        "numerop": datos[1],
                        "ingredientes": datos[2].split(",") if datos[2] else []
                    })
    except FileNotFoundError:
        with open("tablaPizza.txt", "w", encoding="utf-8") as archivo:
            pass
    return carrito

def QuitarTabla():
    open("tablaPizza.txt", "w").close()

def eliminarPizzaEspecifica(indice):
    tabla = colocarTabla()
    if 0 <= indice < len(tabla):
        tabla.pop(indice)
        with open("tablaPizza.txt", "w", encoding="utf-8") as archivo:
            for pizza in tabla:
                ingredientes_lista = ",".join(pizza["ingredientes"])
                archivo.write(
                    f"{pizza['tamanio']}|{pizza['numerop']}|{ingredientes_lista}\n")
        return True
    return False
@app.route('/eliminar_pizza/<int:indice>', methods=['POST'])
def eliminar_pizza(indice):
    if eliminarPizzaEspecifica(indice):
        flash("Se quitó la pizza de la", "success")
    else:
        flash("No se pudo eliminar la pizza", "danger")
    return redirect(url_for('index'))


PRECIOS = {
    'pequena': 40,
    'mediana': 80,
    'grande': 120
}

INGREDIENTE_PRECIO = 10


@app.route('/finalizarPedido', methods=['GET', 'POST'])
def finalizarPedido():
    formularioP = colocarTabla()
    formularioC = forms.UserForm(request.form)

    if not formularioP:
        flash("No hay pizzas en la tabla", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        if formularioC.validate_on_submit():
            nombre = formularioC.nombre.data
            direccion = formularioC.direccion.data
            telefono = formularioC.telefono.data

            session['cliente_data'] = {
                'nombre': nombre,
                'direccion': direccion,
                'telefono': telefono
            }
        elif 'cliente_data' in session:
            nombre = session['cliente_data'].get('nombre')
            direccion = session['cliente_data'].get('direccion')
            telefono = session['cliente_data'].get('telefono')
        else:
            flash("Completar los datos del cliente", "danger")
            return redirect(url_for('index'))

        if not nombre or not direccion or not telefono:
            flash("Completar los datos del cliente", "danger")
            return redirect(url_for('index'))

        subtotal_total = 0
        for pizza in formularioP:
            precio_inicial = PRECIOS[pizza["tamanio"]]
            precio_ingredientes = len(
                pizza["ingredientes"]) * INGREDIENTE_PRECIO
            subtotal_pieza = precio_inicial + precio_ingredientes
            subtotal_total += subtotal_pieza * int(pizza["numerop"])

        nueva_venta = Cliente(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            total=subtotal_total
        )
        

        db.session.add(nueva_venta)
        db.session.flush()

        for pizza in formularioP:
            precio_inicial = PRECIOS[pizza["tamanio"]]
            precio_ingredientes = len(
                pizza["ingredientes"]) * INGREDIENTE_PRECIO
            subtotal_pieza = precio_inicial + precio_ingredientes
            subtotal_total_pizza = subtotal_pieza * int(pizza["numerop"])

            detalle = DetallePizza(
                idCliente=nueva_venta.id,
                tamanio=pizza["tamanio"],
                numerop=pizza["numerop"],
                subtotal=subtotal_total_pizza
            )

           


            db.session.add(detalle)
            db.session.flush()

            for ingrediente in pizza["ingredientes"]:
                ing = IngredientePizza(
                    detalle_pizza_id=detalle.id,
                    nombre_ingrediente=ingrediente
                )
                db.session.add(ing)

        try:
            db.session.commit()
            QuitarTabla()
            flash("Venta generada exitosamente", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error en el proceso de venta: {str(e)}", "danger")
            return redirect(url_for('index'))
    return redirect(url_for('index'))

if __name__ == '__main__':
	csrf.init_app(app)
	db.init_app(app)

	with app.app_context():
		db.create_all()
	app.run(debug=True)