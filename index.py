import pandas as pd
import re
import os
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

directory_path = os.getcwd()

def process_text_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        second_line = lines[1].strip()

    date_match = re.search(r'du (\d{2})(\d{2})(\d{2}) sur', second_line)

    if date_match:
        day = date_match.group(1)
        month = date_match.group(2)
        year = f"20{date_match.group(3)}"
        formatted_date = f"{day}/{month}/{year}"
    else:
        formatted_date = ''

    data = []
    for line in lines[2:]:
        if line.startswith(('1%', '2%')):
            parts = re.findall(r'\S+', line)
            if len(parts) == 2:
                data.append(parts)
    
    df = pd.DataFrame(data, columns=["Defects", "Recurrence"])
    df['Reference'] = df['Defects'].str[:2]
    df['Type'] = df['Defects'].str[2:]
    df.drop('Defects', axis=1, inplace=True)
    df = df[['Reference', 'Type', 'Recurrence']]
    df['Recurrence'] = pd.to_numeric(df['Recurrence'], errors='coerce').fillna(0).astype(int)
    df['Formatted Date'] = formatted_date

    return df


excel_files = [file for file in os.listdir(directory_path) if file.endswith(('.xlsx', '.txt'))]

combined_data = pd.DataFrame()

for file in excel_files:
    file_path = os.path.join(directory_path, file)
    df = process_text_file(file_path)
    combined_data = pd.concat([combined_data, df])

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive Dashboard"),
    dcc.Dropdown(
        id='date-dropdown',
        options=[{'label': 'All Dates', 'value': 'All Dates'}] +
                [{'label': date, 'value': date} for date in sorted(combined_data['Formatted Date'].unique()) if 'Formatted Date' in combined_data],
        multi=True,
        value=['All Dates'],
        placeholder="Select a date to filter",
    ),
    dcc.Graph(id='main-chart')
])

@app.callback(
    Output('main-chart', 'figure'),
    [Input('date-dropdown', 'value')]
)
def update_chart(selected_dates):
    if not selected_dates:
        selected_dates = ['All Dates']
        
    # Create an empty figure
    combined_fig = px.scatter()
    
    for date in selected_dates:
        if date == 'All Dates':
            fig = px.bar(combined_data, x='Type', y='Recurrence', color='Reference', title='Defect Recurrence by Type (All Dates)')
            combined_fig.add_trace(fig['data'][0])
        else:
            filtered_df = combined_data[combined_data['Formatted Date'] == date]
            fig = px.bar(filtered_df, x='Type', y='Recurrence', color='Reference', title=f'Defect Recurrence by Type - {date}')
            combined_fig.add_trace(fig['data'][0])

    combined_fig.update_layout(title='Combined Chart')
    return combined_fig

if __name__ == '__main__':
    app.run_server(debug=True)