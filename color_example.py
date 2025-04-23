import streamlit as st
import pandas as pd
import numpy as np

# Create a sample DataFrame
np.random.seed(0)
df = pd.DataFrame({
    'A': np.random.randn(5),
    'B': np.random.randint(0, 10, 5),
    'C': ['Low', 'High', 'Medium', 'High', 'Low']
})

# Function to apply background color based on value
def highlight_column(val, color='yellow'):
    return f'background-color: {color}'

# Apply style based on column type
styled_df = df.style.apply(
    lambda x: [highlight_column(x.iloc[i], 'lightcoral') if isinstance(x.iloc[i], (int, float)) and x.iloc[i] < 0 
               else highlight_column(x.iloc[i], 'lightgreen') if isinstance(x.iloc[i], (int, float)) and x.iloc[i] >= 0
               else '' for i in range(len(x))],
    axis=1
)

# Display the styled DataFrame with column configuration
st.dataframe(
    styled_df,
    column_config={
        'A': st.column_config.NumberColumn('Column A'),
        'B': st.column_config.NumberColumn('Column B'),
        'C': st.column_config.TextColumn('Column C'),
    },
    hide_index=True
)  
