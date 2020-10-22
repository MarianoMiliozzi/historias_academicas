##################################### IMPORTING ################################
import pandas as pd;
import json;
import base64;
import io;
import plotly.graph_objs as go;
import dash;
import dash_table;
from dash.dependencies import Output, Input, State
import dash_core_components as dcc;
import dash_html_components as html
from collections import defaultdict

# ademas importamos la funcion de consulta.py que ejecuta las querys SQL
import assets.consulta as consulta;

##################################### IMPORTING ################################
#################################### CONSULTA DB ###############################

# nacion = pd.read_csv('assets/nacionalidades.csv',encoding='latin',sep='|')
# nacion_dic = {nacion.cod_nacionalidad.iloc[i]:nacion.nacionalidad.iloc[i] for i in range(len(nacion))}

#################################### CONSULTA DB ###############################
#################################### RAW PYTHON  ###############################


################################### RAW PYTHON ###############################
################################## APP SETTING ###############################
# seteamos la url del ccs
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# instanciamos la app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# le definimos un título
app.title = 'Historia Académica'
# instanciamos el servidor
server = app.server  # the Flask app

freedb = pd.DataFrame()
################################## APP SETTING ###############################
################################## APP LAYOUT ################################
app.layout = \
    html.Div(className='cuerpo',
             children=[
                 html.Div(className='row',
                          children=[
                              html.H4('Estado de Titulaciones de POSGRADOS', className='eight columns'),
                              html.Img(src='/assets/untref_logo.jpg',
                                       className='four columns',
                                       style={'margin-top': '13px'}),
                              ]),

                 # INPUT DOCUMENTO
                 html.Div(id='div-input-alumno',
                          children=[
                              dcc.Input(id='user-input',
                                        placeholder='Ingrese un Documento',
                                        ),
                              html.Div(id='div-submit-button',
                                       children=[
                                           html.Button(id='submit-button',
                                                       children='Buscar',
                                                       ),
                                           ]
                                       ),
                              html.Div(id='div-clear-button',
                                       hidden=True,
                                       children=[
                                           html.Button(id='clear-button',
                                                       children='Nueva Busqueda',
                                                       ),
                                           ]
                                       )
                              ]),

    # TABLA DE CARRERAS POR ALUMNO
    html.Div(id='div-alumno-elegido',
             # className='row',
             # style={'text-align':'center',
             #        'align-content':'center'},
             hidden=True,
             children=[
                 html.Hr(),
                 html.H5(id='content-label'),

                 html.Div(id='div-container-tabla-carreras',
                          className='row',
                          style={'text-align': 'center',
                                 'align-content': 'center'},
                          children=[
                              html.Hr(),
                              # div para la tabla de carreras del alumno
                              html.Div(
                                       children=[
                                           dash_table.DataTable(
                                               id='tabla-carreras',
                                               row_selectable="single",
                                               include_headers_on_copy_paste=True,
                                              # GENERL STYLE
                                              style_cell={
                                                  'textAlign': 'left',
                                              },
                                              style_data={'whiteSpace': 'pre-line'},

                                              # ancho columnas
                                              style_cell_conditional=[
                                                  {
                                                      'if': {'column_id': 'carrera'},
                                                      'textAlign': 'center',
                                                      'fontWeight': 'bold',
                                                      'width': '300px',
                                                  },
                                                  {
                                                      'if': {'column_id': ['persona']},
                                                      'textAlign': 'center',
                                                      'width': '120px',
                                                  },
                                                  {
                                                      'if': {'column_id': ['nivel']},
                                                      'textAlign': 'center',
                                                      'width': '200px',
                                                  }],
                                          # ## STRIPED ROWS
                                          # style_data_conditional=[
                                          #     {
                                          #         'if': {'row_index': 'odd'},
                                          #         'backgroundColor': 'rgb(248, 248, 248)',
                                          #     }
                                          # ],
                                          # ## HEADER
                                          # style_header={
                                          #     'backgroundColor': 'rgb(230, 230, 230)',
                                          #     'fontWeight': 'bold'
                                          # },

                                      ), ]
                              ),
                          ]
                          ),



             ]
             ),


    # TABLA DE PLANES POR ALUMNO
    html.Div(id='div-plan-elegido',
          # className='row',
          # style={'text-align':'center',
          #        'align-content':'center'},
          hidden=True,
          children=[
              html.Div(id='div-container-tabla-planes',
                       className='row',
                       style={'text-align': 'center',
                              'align-content': 'center'},
                       children=[
                           html.Hr(),

                           # div para la tabla de carreras del alumno
                           html.Div(
                               children=[
                                   dash_table.DataTable(
                                       id='tabla-planes',
                                       row_selectable="single",
                                       include_headers_on_copy_paste=True,
                                       # GENERL STYLE
                                       style_cell={
                                           'textAlign': 'left',
                                       },
                                       style_data={'whiteSpace': 'pre-line'},

                                       # ancho columnas
                                       # style_cell_conditional=[
                                       #     {
                                       #         'if': {'column_id': 'carrera'},
                                       #         'textAlign': 'center',
                                       #         'fontWeight': 'bold',
                                       #         'width': '300px',
                                       #     },
                                       #     {
                                       #         'if': {'column_id': ['persona']},
                                       #         'textAlign': 'center',
                                       #         'width': '120px',
                                       #     },
                                       #     {
                                       #         'if': {'column_id': ['nivel']},
                                       #         'textAlign': 'center',
                                       #         'width': '200px',
                                       #     }],
                                       # ## STRIPED ROWS
                                       # style_data_conditional=[
                                       #     {
                                       #         'if': {'row_index': 'odd'},
                                       #         'backgroundColor': 'rgb(248, 248, 248)',
                                       #     }
                                       # ],
                                       # ## HEADER
                                       # style_header={
                                       #     'backgroundColor': 'rgb(230, 230, 230)',
                                       #     'fontWeight': 'bold'
                                       # },

                                   ), ]
                           ),
                       ]
                       ),
          ]
          ),
])


################################ APP LAYOUT ##################################
################################ CALL BACKS ##################################

@app.callback(
    [
        Output('div-clear-button', 'hidden'),
        Output('div-submit-button', 'hidden'),

        Output('user-input', 'disabled'),
        Output('user-input', 'value'),
        Output('tabla-carreras', 'selected_rows'),
    ],
    [
        Input('submit-button', 'n_clicks'),
        Input('clear-button', 'n_clicks'),
    ],
    [
        State('user-input', 'value')
    ]
)
def stage_manager(submit,clear,input):
    # detectamos el ultimo boton presionado
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    ctx_msg = json.dumps({
        'states': ctx.states,
        'triggered': ctx.triggered,
        'inputs': ctx.inputs
    }, indent=2)

    if button_id == 'submit-button':
        return [False, True, True,input,[]]
    elif button_id == 'clear-button':
        return [True, False, False, None, []]
    else:
        return [True, False, False, None,[]]




@app.callback(
    [
        Output('content-label', 'children'),

        Output('div-alumno-elegido', 'hidden'),
        Output('tabla-carreras', 'data'),
        Output('tabla-carreras', 'columns'),

        Output('div-plan-elegido', 'hidden'),
        Output('tabla-planes', 'data'),
        Output('tabla-planes', 'columns'),

    ],
    [
        Input('submit-button', 'n_clicks'),
        Input('tabla-carreras', 'derived_virtual_selected_rows'),
     ],
    [State('user-input', 'value'),],

)

def seleccion_alumno(submit,selected_row,alumno):

    # antes de ingresar ningun dato
    if (alumno != None) & (alumno != ''):

        # convertimos al alumno para que pueda realizar la consulta en sql
        alumno = "'"+str(alumno)+"'"

        # ejecutamos la consulta y nos traemos todas las tablas
        persona_status, persona_nombre, carreras_alumno, resumen, analiticos = consulta.get_data_documento(alumno)

        # generamos diccionarios para renombrar las columnas
        dic_carreras_alumno = {'persona': 'Persona', 'carrera': 'Carrera', 'sigla': 'Sigla', 'plan_nombre': 'Plan', 'plan_version': 'Plan Version',
                               'materias_totales': 'Requeridas', 'materias_aprobadas': 'Aprobadas', 'porcentaje': '%'}

        # si es una persona válida (DOCUMENTO)
        if persona_status:
            # acomodamos datos de las tablas
            try:
                carreras_alumno['porcentaje'] = (carreras_alumno.materias_aprobadas / carreras_alumno.materias_totales) * 100
                carreras_alumno.porcentaje = carreras_alumno.porcentaje.astype(int)

                carreras_alumno = carreras_alumno.drop(['nivel', 'alumno', 'calidad', 'codigo'], axis=1)
                filas_planes = carreras_alumno.plan_version.to_dict()
            except:
                pass
            # limpiamos algunas columnas

            # si hay una fila seleccionada (carrera)
            if selected_row != []:

                selected_row = selected_row[0]

                analiticos = analiticos.drop_duplicates('actividad_codigo')

                tabla_analitico = pd.DataFrame()
                for i in range(len(resumen.loc[resumen.plan_version == filas_planes[selected_row]])):

                    for i in resumen.loc[resumen.plan_version == filas_planes[selected_row]].lista_materias.iloc[i]:
                        tabla_analitico = pd.concat([tabla_analitico, analiticos.loc[analiticos.actividad_codigo == i]])
                try:
                    carreras_alumno = carreras_alumno.drop('plan_version', axis=1)
                    tabla_analitico = tabla_analitico.drop(['plan_version','resultado','estado'],axis=1)
                except:
                    pass

                return [
                    persona_nombre,
                    False,
                    carreras_alumno.to_dict('records'),
                    [{"name": dic_carreras_alumno[i], "id": i} for i in carreras_alumno.columns],
                    False,
                    tabla_analitico.to_dict('records'),
                    [{"name": i, "id": i} for i in tabla_analitico.columns],
                    ]

            # si NO hay una fila seleccionada (carrera)
            else:
                return [
                    persona_nombre,
                    False,
                    carreras_alumno.to_dict('records'),
                    [{"name": dic_carreras_alumno[i], "id": i} for i in carreras_alumno.columns],
                    True,
                    freedb.to_dict('records'),
                    [{"name": i, "id": i} for i in freedb.columns],
                    ]
        # si no una persona válida (DOCUMENTO)
        else:
            try:
                carreras_alumno = carreras_alumno.drop('plan_version', axis=1)
            except:
                pass
            return [
                'No es persona',
                False,
                freedb.to_dict('records'),
                [{"name": i, "id": i} for i in freedb.columns],
                True,
                freedb.to_dict('records'),
                [{"name": i, "id": i} for i in freedb.columns],
            ]
    # si Alumno == NONE or '' -> INITIAL CALLBACK
    else:
        return ['',
                True,
                freedb.to_dict('records'),
                [{"name": i, "id": i} for i in freedb.columns],
                True,
                freedb.to_dict('records'),
                [{"name": i, "id": i} for i in freedb.columns],
                ]


################################ CALL BACKS ##################################
################################# APP LOOP ###################################
if __name__ == '__main__':
    app.run_server(debug=True)
