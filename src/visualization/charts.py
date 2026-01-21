# src/visualization/charts.py
import plotly.express as px



def generate_chart(df, chart_type="bar"): #Placeholder
    if df.empty:
        return None
    
    if chart_type == "bar":
        fig = px.bar(
            df,
            x=df.columns[1], 
            y=df.columns[0],  
            orientation='h',
            title='Bar Chart',
            color=df.columns[0],
            color_continuous_scale='Blues'
        )
    elif chart_type == "line":
        fig = px.line(
            df,
            x=df.columns[0],
            y=df.columns[1],
            title='Line Chart'
        )
    else:
        fig = px.bar(
            df,
            x=df.columns[1],
            y=df.columns[0],
            title='Default Bar Chart'
        )

    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='closest',
        plot_bgcolor='white',
        font=dict(size=12)
    )

    return fig
