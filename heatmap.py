'''
Genera un mapa de calor basado en datos de contaminantes,
viento y coordenadas de estaciones de calidad del aire.
'''

import pandas as pd
import plotly
import plotly.graph_objects as go

from kriging import interpolate

def plot_heatmap(pollutant: str, day: str) -> None:
    '''
    Muestra el mapa de calor del contaminante (pollutant) el día (day) en el navegador.
    '''

    # columnas a extraer del CSV
    columns = ['timestamp', 'station', pollutant, 'velocity', 'direction']
    dataframe = pd.read_csv('filled.csv', usecols=columns).dropna()
    # leer las coordenadas de las estaciones
    coords = pd.read_csv('coords.csv')

    # filtrar registros del día elegido
    dataset = coords.merge(dataframe.loc[dataframe['timestamp'].str.startswith(day)], on='station')
    # convertir strings a objeto datetime
    strfdt = '%d-%b-%y %H'
    dataset['timestamp'] = pd.to_datetime(dataset['timestamp'], format=strfdt)
    # escala de densidad
    pollutionmin, pollutionmax = min(dataset[pollutant]), max(dataset[pollutant])

    frames, steps = [], []
    # filtrar horas del día elegido
    hours = dataset.timestamp.unique()
    hours.sort()
    for hour in hours:
        # coordenadas de las estaciones y el contaminante que leyeron en la hora epecífica
        data = dataset.loc[dataset['timestamp'] == hour]

        # método de kringing
        # interpolar contaminante
        xcoords, ycoords, zpollution = interpolate(data.lon, data.lat, data[pollutant], range(5, 41, 5))

        # rango para interpolación recursiva para valores de viento (20x20 puntos)
        grid = range(5, 21, 5)
        # interpolar velocidad de viento
        xvelocity, yvelocity, zvelocity = interpolate(data.lon, data.lat, data['velocity'], grid)
        # interpolar dirección de viento
        xdirection, ydirection, zdirection = interpolate(data.lon, data.lat, data['direction'], grid)

        strhour = pd.to_datetime(hour).strftime(strfdt)
        
        frames.append({
            'name': f'frame_{strhour}',
            'data': [
                # mapa de vectores de viento
                dict (
                    type = 'scattermapbox',
                    lon = xdirection,
                    lat = ydirection,
                    mode = 'markers',
                    marker = dict(
                        symbol = 'marker',
                        size = 10,
                        allowoverlap=True,
                        angle = [angle + 180 for angle in zdirection], 
                    ),
                    text = zdirection,
                ),
                # mapa de velocidad de viento
                dict(
                    type='scattermapbox',
                    lon=xvelocity,
                    lat=yvelocity,
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=6,
                        allowoverlap=True,
                        color='rgb(255, 0, 0)',
                        cmin=0,
                        cmax=60,
                        autocolorscale=True,
                        coloraxis='coloraxis'
                    ),
                    text=zvelocity
                ),
                # mapa de calor de densidad de contaminante
                dict (
                    type = 'densitymapbox',
                    lon = xcoords,
                    lat = ycoords,
                    z = zpollution,
                    opacity = 0.5,
                    zmin = pollutionmin,
                    zmax = pollutionmax                
                    )
            ]
        })
        steps.append({
            'label': strhour,
            'method': 'animate',
            'args': [
                [f'frame_{strhour}'],
                {
                    'mode': 'immediate',
                    'frame': {
                        'duration': 200,
                        'redraw': True
                    },
                    'transition': {'duration': 100}
                }
            ]
        })

    sliders = [{
        'transition': {'duration': 0},
        'x': 0.08,
        'len': 0.88,
        'currentvalue': {'xanchor': 'center'},
        'steps': steps
    }]

    playbtn = [{
        'type': 'buttons',
        'showactive': True,
        'x': 0.045, 'y': -0.08,
        'buttons': [{
            'label': 'Play',
            'method': 'animate',
            'args': [
                None,
                {
                    'mode': 'immediate',
                    'frame': {
                        'duration': 200,
                        'redraw': True
                    },
                    'transition': {'duration': 100},
                    'fromcurrent': True
                }
            ]
        }]
    }]

    with open('mytoken.txt', 'r') as file:
        token = file.read()

    layout = go.Layout(
        sliders=sliders,
        updatemenus=playbtn,
        # mapbox_style='stamen-terrain',
        autosize=True,
        mapbox=dict(
            accesstoken = token,
            center=dict(lat=25.67, lon=-100.338),
            zoom=9.3
        )
    )

    data = frames[0]['data']
    figure = go.Figure(data=data, layout=layout, frames=frames)
    plotly.offline.plot(figure, filename=f'results/{pollutant}_{day}.html')
    # figure.show()