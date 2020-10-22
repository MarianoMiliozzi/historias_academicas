import numpy as np; import pandas as pd; import time; import datetime
import psycopg2, psycopg2.extras; import os; from collections import defaultdict

dic_operaciones = {'I': 'Insert', 'U': 'Update', 'D': 'Delete'}

# Esta celda permite obtener toda la tabla que sea seleccionada (el orden de las columnas varía desde la db hacia aqui)
# elegimos el origen
data_db = 'guarani3162posgrado'
#data_db = 'guarani3162posgradoprueba'

# nos conectamos a la base seleccionada en data
conn = psycopg2.connect(database=data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
cur = conn.cursor()

cur.execute(
    '''SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA in ('negocio','negocio_pers') ''')
tablas = pd.DataFrame(cur.fetchall())
conn.close()

def get_table(esquema, tabla_objetivo, columns, where):
    ''' toma como parametros: esquema, tabla_objetivo, columns, where
    esquema y tabla_objetivo son variables definidas, y columns es una lista de columnas filtrada de tablas[0]
    siempre se trabajará con la base de datos declarada en data_db al inicio de esta notebook.
    '''
    global out
    conn = psycopg2.connect(database=data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
    cur = conn.cursor()

    if where == '':
        if columns == '*':
            cur.execute('SELECT {} FROM {}.{}'.format(columns, esquema, tabla_objetivo))
            out = pd.DataFrame(cur.fetchall(), columns=list(
                tablas.loc[(tablas[0] == esquema) & (tablas[1] == tabla_objetivo)][2]))
        else:
            cur.execute('SELECT {} FROM {}.{}'.format(', '.join(columns), esquema, tabla_objetivo))
            out = pd.DataFrame(cur.fetchall(), columns=columns)
    else:
        if columns == '*':
            cur.execute('SELECT {} FROM {}.{} WHERE {}'.format(columns, esquema, tabla_objetivo, where))
            out = pd.DataFrame(cur.fetchall(), columns=list(
                tablas.loc[(tablas[0] == esquema) & (tablas[1] == tabla_objetivo)][2]))

        else:
            cur.execute('SELECT {} FROM {}.{} WHERE {}'.format(', '.join(columns), esquema, tabla_objetivo, where))
            out = pd.DataFrame(cur.fetchall(), columns=columns)
    # cerrar siempre la conexion por las dudas...
    conn.close()
    return out.tail(3)

freedb = pd.DataFrame()

# traigo los datos de todas las propuestas
get_table('negocio','sga_propuestas',['propuesta','nombre','nombre_abreviado','codigo'],'')
propuestas_total = out.copy()

propuestas_total.columns = ['propuesta', 'carrera', 'sigla', 'codigo']
propuestas_total['nivel'] = [propuestas_total.carrera.iloc[i].split(' ')[0] for i in range(len(propuestas_total))]

# traigo las condiciones de los certificados, solo una vez
get_table('negocio','vw_condiciones','*','')
dic_condicion = {out.elemento.iloc[i] : out.parametros.iloc[i] for i in range(len(out))}

# traigo los datos de todas las materias
get_table('negocio','sga_elementos',['elemento','nombre','codigo'],'entidad_subtipo in (50, 52)')
materias_total = out.copy()

elementos_target = list(materias_total.elemento.unique())
elementos_target = [str(i) for i in elementos_target]
sql_elementos = "'" + "','".join(elementos_target) + "'"

# traigo los datos de todas las materias
get_table('negocio','sga_elementos_atrib',['elemento','horas_totales'],'elemento in ({})'.format(sql_elementos))
horas = out.copy()

materias_total = materias_total.merge(horas)


def get_data_documento(documento):
    # obtengo los datos de la persona, si no existe vuelve un db vacio
    get_table('negocio', 'vw_personas', ['persona', 'apellido', 'nombres'], 'nro_documento = {}'.format(documento))

    # chequeo que haya datos en el db y asigno el status para cancelar la consulta en caso que no haya
    try:
        persona = out.persona.iloc[0]
        persona_nombre = out.apellido.iloc[0] + ', ' + out.nombres.iloc[0].title()
        persona_status = True
    except:
        persona = 'no es persona'
        persona_status = False

    # si la persona existe ejecuta la consulta
    if persona_status:
        # obtengo los datos de la inscripcion del alumno
        get_table('negocio', 'sga_alumnos', ['alumno', 'persona', 'propuesta', 'plan_version', 'calidad'],
                  'persona = {}'.format(persona))
        carreras_alumno = out.copy()

        #### nombre y apellido
        carreras_alumno['persona'] = persona_nombre

        #### propuestas del alumno
        carreras_alumno = carreras_alumno.merge(propuestas_total).drop(['propuesta'], axis=1)

        #### filtramos cursos y diplomaturas
        carreras_alumno = carreras_alumno.loc[carreras_alumno.nivel.isin(['Maestría', 'Especialización', 'Doctorado'])]
        carreras_alumno.reset_index(inplace=True, drop=True)

        #### planes del alumno
        plan_target = (carreras_alumno.plan_version.unique())
        plan_target = [str(i) for i in plan_target]
        sql_planes = "'" + "','".join(plan_target) + "'"

        ##### planes -> total de materias
        if len(plan_target) > 0:

            get_table('negocio', 'sga_planes_versiones', ['plan_version', 'nombre'],
                      'plan_version in ({})'.format(sql_planes))
            planes_nombre = out.copy()
            planes_nombre.columns = ['plan_version', 'plan_nombre']
            carreras_alumno = carreras_alumno.merge(planes_nombre)



            get_table('negocio', 'vw_componentes_modulo_plan', '*', 'plan_version in ({})'.format(sql_planes))
            plan = out.loc[out.modulo_nombre != 'Raíz del plan'].copy()
            plan['cantidad_requerida'] = plan.modulo_elemento.map(dic_condicion)
            plan.cantidad_requerida.fillna(
                plan.modulo_elemento.map(lambda x: plan.groupby('modulo_elemento')['modulo_nombre'].count()[x]),
                inplace=True)
            plan_modulos = plan.drop_duplicates(subset='modulo_elemento')[
                ['plan_version', 'modulo_nombre', 'cantidad_requerida']]
            resumen = plan.groupby(['plan_version', 'modulo_nombre'])['codigo'].apply(list).reset_index(
                name='lista_materias')
            resumen['materias_totales'] = [len(i) for i in resumen.lista_materias]
            resumen = resumen.merge(plan_modulos, how='outer', on=['plan_version', 'modulo_nombre'])
            resumen['cantidad_requerida'] = resumen.cantidad_requerida.astype(int)
            plan_short = resumen.groupby('plan_version')['cantidad_requerida'].sum().reset_index(
                name='materias_totales')

            ### total de materias por carrera
            carreras_alumno = carreras_alumno.merge(plan_short)

            ##### materias aprobadas
            alumnos = list(carreras_alumno.alumno.astype(str).unique())
            alumnos_target = (carreras_alumno.alumno.unique())
            alumnos_target = [str(i) for i in alumnos_target]
            sql_alumnos = "'" + "','".join(alumnos_target) + "'"

            dic_origenes = {"A": "Aprobación por Resolución", "B": "Equivalencias Totales",
                            "C": "Equivalencias de Regularidad", "D": "Equivalencias Parciales", "E": "Examen",
                            "P": "Promociones", "R": "Regulares"}

            # NEW !!!!
            get_table('negocio', 'sga_actas_detalle', ['id_acta', 'alumno', 'plan_version', 'fecha', 'nota', 'resultado'],
                      'alumno in ({})'.format(sql_alumnos))
            acta_detalle = out.copy()
            acta_detalle.shape
            actas_target = list(acta_detalle.id_acta.unique())
            actas_target = [str(i) for i in actas_target]
            sql_actas = "'" + "','".join(actas_target) + "'"
            get_table('negocio', 'sga_actas', ['id_acta', 'origen', 'llamado_mesa'], 'id_acta in ({})'.format(sql_actas))
            actas = out.copy()
            llamado_target = list(actas.llamado_mesa.unique())
            llamado_target = [str(i) for i in llamado_target]
            sql_llamado = "'" + "','".join(llamado_target) + "'"
            get_table('negocio', 'sga_llamados_mesa', ['llamado_mesa', 'mesa_examen'],
                      'llamado_mesa in ({})'.format(sql_llamado))
            llamados = out.copy()
            mesa_target = list(llamados.mesa_examen.unique())
            mesa_target = [str(i) for i in mesa_target]
            sql_mesa = "'" + "','".join(mesa_target) + "'"
            get_table('negocio', 'sga_mesas_examen', ['mesa_examen', 'nombre', 'elemento', 'anio_academico'], 'mesa_examen in ({})'.format(sql_mesa))
            mesas = out.copy()
            acta_detalle = acta_detalle.merge(actas)
            acta_detalle = acta_detalle.merge(llamados)
            acta_detalle = acta_detalle.merge(mesas)
            acta_detalle['actividad_codigo'] = [acta_detalle.nombre.iloc[i].split('_')[0] for i in range(len(acta_detalle))]

            analiticos = acta_detalle.copy()
            analiticos = analiticos.loc[analiticos.resultado == 'A']

            aprobadas = analiticos.groupby('plan_version')[['resultado']].count()
            aprobadas.columns = ['materias_aprobadas']
            aprobadas.reset_index(inplace=True)
            codigos_alumno = list(analiticos.actividad_codigo.unique())

            analiticos = analiticos.drop(['alumno','plan_version','llamado_mesa','mesa_examen','nombre','anio_academico'],axis=1)
            analiticos = analiticos.merge(materias_total)
            analiticos = analiticos[['fecha', 'id_acta','actividad_codigo', 'nombre','origen', 'nota', 'resultado', 'horas_totales']]



            for i in range(len(resumen)):
                aprobadas = []
                lista = resumen.lista_materias.iloc[i]
                for mat in lista:
                    if mat in codigos_alumno:
                        aprobadas.append(True)
                resumen.loc[i, 'aprobadas'] = sum(aprobadas)

            carreras_alumno = carreras_alumno.merge(
                resumen.groupby('plan_version')['aprobadas'].sum().reset_index(name='materias_aprobadas'))



            return [persona_status, persona_nombre, carreras_alumno, resumen, analiticos]

        else:
            return [persona_status, 'La persona no posee Inscripciones', freedb, freedb, freedb]

    # si no es persona devuelve lo siguiente
    else:
        return [persona_status, '', freedb, freedb, freedb]