from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import mysql.connector

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'vitalsoft_secret_key'  # Para manejar sesiones

# Habilitar CORS
CORS(app)

# Configuración de la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='vitalsoft'
    )

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener datos del formulario
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        
        # Validar con la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id_usuario, nombre, tipo_usuario, contrasena FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if usuario and usuario['contrasena'] == contrasena:
            # Guardar información del usuario en la sesión
            session['usuario_id'] = usuario['id_usuario']
            session['nombre'] = usuario['nombre']
            session['tipo_usuario'] = usuario['tipo_usuario']
            
            # Redirigir según el tipo de usuario
            if usuario['tipo_usuario'] == 'paciente':
                return redirect(url_for('paciente_dashboard'))
            elif usuario['tipo_usuario'] == 'medico':
                return redirect(url_for('medico_dashboard'))
            elif usuario['tipo_usuario'] == 'empleado':
                return redirect(url_for('empleado_dashboard'))
        
        return render_template('login.html', error="Credenciales incorrectas")
    
    return render_template('login.html')

# Dashboards
@app.route('/paciente/dashboard')
def paciente_dashboard():
    if 'usuario_id' not in session or session['tipo_usuario'] != 'paciente':
        return redirect(url_for('login'))
    return render_template('paciente/dashboard.html')

@app.route('/medico/dashboard')
def medico_dashboard():
    if 'usuario_id' not in session or session['tipo_usuario'] != 'medico':
        return redirect(url_for('login'))
    return render_template('medico/dashboard.html')

@app.route('/empleado/dashboard')
def empleado_dashboard():
    if 'usuario_id' not in session or session['tipo_usuario'] != 'empleado':
        return redirect(url_for('login'))
    return render_template('empleado/dashboard.html')

# API - Citas
@app.route('/api/paciente/citas/<int:paciente_id>', methods=['GET'])
def get_citas_paciente(paciente_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT c.id_cita, c.fecha, c.hora, c.estado, c.tipo_cita, c.motivo,
               CONCAT(u.nombre, ' ', u.apellido) as medico, m.especialidad
        FROM citas c
        JOIN medicos m ON c.id_medico = m.id_medico
        JOIN usuarios u ON m.id_usuario = u.id_usuario
        WHERE c.id_paciente = %s
        ORDER BY c.fecha, c.hora
    """
    cursor.execute(query, (paciente_id,))
    citas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(citas)

@app.route('/api/citas', methods=['POST'])
def crear_cita():
    datos = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO citas (id_paciente, id_medico, fecha, hora, tipo_cita, motivo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            datos['id_paciente'],
            datos['id_medico'],
            datos['fecha'],
            datos['hora'],
            datos['tipo_cita'],
            datos['motivo']
        ))
        
        conn.commit()
        respuesta = {'success': True, 'message': 'Cita agendada correctamente'}
    except Exception as e:
        conn.rollback()
        respuesta = {'success': False, 'message': str(e)}
    
    cursor.close()
    conn.close()
    
    return jsonify(respuesta)

# API - Historial médico
@app.route('/api/paciente/<int:paciente_id>/historial', methods=['GET'])
def get_historial_paciente(paciente_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener ID del historial del paciente
    query_historial = "SELECT id_historial FROM historiales_medicos WHERE id_paciente = %s"
    cursor.execute(query_historial, (paciente_id,))
    historial = cursor.fetchone()
    
    if not historial:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Historial no encontrado'})
    
    id_historial = historial['id_historial']
    
    # Obtener consultas del historial
    query_consultas = """
        SELECT c.id_consulta, c.fecha_consulta, c.diagnostico, c.tratamiento,
               CONCAT(u.nombre, ' ', u.apellido) as medico, m.especialidad
        FROM consultas c
        JOIN medicos m ON c.id_medico = m.id_medico
        JOIN usuarios u ON m.id_usuario = u.id_usuario
        WHERE c.id_historial = %s
        ORDER BY c.fecha_consulta DESC
    """
    cursor.execute(query_consultas, (id_historial,))
    consultas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'consultas': consultas})

# Iniciar el servidor
if __name__ == '__main__':
    app.run(debug=Tr
